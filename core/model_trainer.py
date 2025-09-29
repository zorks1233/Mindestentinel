# src/core/model_trainer.py
"""
model_trainer.py - Modelltrainer für Mindestentinel

Diese Datei implementiert das Training neuer Modelle basierend auf gesammeltem Wissen.
"""

import logging
import os
import time
import datetime
import torch
from typing import Dict, Any, Optional, List, Tuple
from transformers import AutoModelForCausalLM, AutoTokenizer, TrainingArguments, Trainer
import json

logger = logging.getLogger("mindestentinel.model_trainer")

class ModelTrainer:
    """
    Trainiert neue Modelle basierend auf gesammeltem Wissen.
    
    Ermöglicht das Training neuer Modelle aus Wissensbeispielen.
    """
    
    def __init__(self, knowledge_base, model_manager, training_config: Optional[Dict[str, Any]] = None):
        """
        Initialisiert den Modelltrainer.
        
        Args:
            knowledge_base: Die Wissensdatenbank
            model_manager: Der ModelManager
            training_config: Optionale Trainingskonfiguration
        """
        self.kb = knowledge_base
        self.mm = model_manager
        self.training_config = training_config or self._default_training_config()
        self.training_active = False
        self.current_training = None
        logger.info("ModelTrainer initialisiert.")
    
    def _default_training_config(self) -> Dict[str, Any]:
        """Gibt die Standard-Trainingskonfiguration zurück."""
        return {
            "epochs": 3,
            "batch_size": 8,
            "learning_rate": 5e-5,
            "max_seq_length": 512,
            "warmup_steps": 500,
            "weight_decay": 0.01,
            "logging_steps": 100,
            "save_steps": 500,
            "evaluation_strategy": "steps",
            "eval_steps": 500,
            "gradient_accumulation_steps": 1,
            "fp16": torch.cuda.is_available(),
            "max_grad_norm": 1.0,
            "early_stopping_patience": 3
        }
    
    def train_new_model(self, goal_id: str, examples: List[Dict[str, Any]]) -> Optional[str]:
        """
        Trainiert ein neues Modell basierend auf gesammelten Beispielen.
        
        Args:
            goal_id: Die ID des Lernziels
            examples: Die Wissensbeispiele
            
        Returns:
            Optional[str]: Der Name des neuen Modells, falls erfolgreich, sonst None
        """
        if self.training_active:
            logger.warning("Training bereits aktiv. Warte auf Abschluss des aktuellen Trainings.")
            return None
        
        self.training_active = True
        self.current_training = {
            "goal_id": goal_id,
            "start_time": datetime.datetime.now().isoformat(),
            "status": "started"
        }
        
        try:
            logger.info(f"Starte Training für neues Modell basierend auf Lernziel {goal_id}...")
            
            # Hole das Basis-Modell (verwende das erste verfügbare Modell)
            base_models = self.mm.list_models()
            if not base_models:
                logger.error("Keine Basis-Modelle für das Training gefunden")
                self._update_training_status("failed", error="Keine Basis-Modelle gefunden")
                return None
            
            base_model_name = base_models[0]
            base_model_info = self.mm.get_model(base_model_name)
            if not base_model_info:
                logger.error(f"Basis-Modell {base_model_name} nicht gefunden")
                self._update_training_status("failed", error=f"Basis-Modell {base_model_name} nicht gefunden")
                return None
            
            # Bereite die Trainingsdaten vor
            train_dataset = self._prepare_training_data(examples)
            if not train_dataset:
                logger.error("Keine gültigen Trainingsdaten erstellt")
                self._update_training_status("failed", error="Keine gültigen Trainingsdaten")
                return None
            
            # Erstelle das neue Modell als Kopie des Basis-Modells
            model = base_model_info["model"].copy()
            tokenizer = base_model_info["tokenizer"]
            
            # Konfiguriere das Training
            training_args = self._create_training_arguments(goal_id)
            
            # Erstelle den Trainer
            trainer = Trainer(
                model=model,
                args=training_args,
                train_dataset=train_dataset,
                tokenizer=tokenizer
            )
            
            # Starte das Training
            logger.info("Starte Training...")
            self._update_training_status("training")
            train_result = trainer.train()
            
            # Speichere das neue Modell
            new_model_name = f"mindest_{goal_id}_{int(time.time())}"
            model_output_dir = os.path.join(self.mm.models_dir, new_model_name)
            
            logger.info(f"Speichere neues Modell unter {model_output_dir}...")
            trainer.save_model(model_output_dir)
            
            # Speichere den Tokenizer
            tokenizer.save_pretrained(model_output_dir)
            
            # Erstelle Metadaten für das neue Modell
            model_metadata = {
                "name": new_model_name,
                "created_at": time.time(),
                "base_model": base_model_name,
                "training_goal": goal_id,
                "training_examples": len(examples),
                "training_duration": (time.time() - self.current_training["start_time"]),
                "training_metrics": {
                    "train_loss": train_result.training_loss,
                    "epoch": train_result.epoch
                },
                "version": "1.0",
                "description": f"Modell trainiert für Lernziel {goal_id}"
            }
            
            # Registriere das neue Modell
            self.mm.register_model(new_model_name, model, tokenizer, model_metadata)
            
            logger.info(f"Neues Modell erstellt: {new_model_name}")
            self._update_training_status("completed", model_name=new_model_name)
            
            return new_model_name
        except Exception as e:
            logger.error(f"Fehler beim Training des Modells: {str(e)}", exc_info=True)
            self._update_training_status("failed", error=str(e))
            return None
        finally:
            self.training_active = False
            self.current_training = None
    
    def _prepare_training_data(self, examples: List[Dict[str, Any]]) -> Optional[Any]:
        """
        Bereitet die Trainingsdaten vor.
        
        Args:
            examples: Die Wissensbeispiele
            
        Returns:
            Optional[Any]: Die vorbereiteten Trainingsdaten, falls erfolgreich, sonst None
        """
        try:
            # Konvertiere die Beispiele in ein Dataset
            formatted_examples = []
            for example in examples:
                # Extrahiere die relevanten Informationen
                prompt = example.get("prompt", "")
                response = example.get("response", "")
                
                # Format für Causal Language Modeling
                text = f"Prompt: {prompt}\nResponse: {response}"
                
                formatted_examples.append({"text": text})
            
            # Erstelle das Dataset
            from datasets import Dataset
            dataset = Dataset.from_dict({"text": [ex["text"] for ex in formatted_examples]})
            
            # Tokenisiere das Dataset
            def tokenize_function(examples):
                return self.tokenizer(examples["text"], padding="max_length", truncation=True, max_length=self.training_config["max_seq_length"])
            
            tokenized_dataset = dataset.map(tokenize_function, batched=True)
            
            return tokenized_dataset
        except Exception as e:
            logger.error(f"Fehler bei der Vorbereitung der Trainingsdaten: {str(e)}", exc_info=True)
            return None
    
    def _create_training_arguments(self, goal_id: str) -> TrainingArguments:
        """
        Erstellt die Trainingsargumente.
        
        Args:
            goal_id: Die ID des Lernziels
            
        Returns:
            TrainingArguments: Die Trainingsargumente
        """
        output_dir = os.path.join(self.mm.models_dir, f"training_{goal_id}_{int(time.time())}")
        
        return TrainingArguments(
            output_dir=output_dir,
            num_train_epochs=self.training_config["epochs"],
            per_device_train_batch_size=self.training_config["batch_size"],
            learning_rate=self.training_config["learning_rate"],
            warmup_steps=self.training_config["warmup_steps"],
            weight_decay=self.training_config["weight_decay"],
            logging_steps=self.training_config["logging_steps"],
            save_steps=self.training_config["save_steps"],
            evaluation_strategy=self.training_config["evaluation_strategy"],
            eval_steps=self.training_config["eval_steps"],
            gradient_accumulation_steps=self.training_config["gradient_accumulation_steps"],
            fp16=self.training_config["fp16"],
            max_grad_norm=self.training_config["max_grad_norm"],
            report_to=["none"]  # Deaktiviere Reporting an externe Dienste
        )
    
    def _update_training_status(self, status: str, **kwargs):
        """
        Aktualisiert den Trainingsstatus.
        
        Args:
            status: Der neue Status
            **kwargs: Zusätzliche Informationen
        """
        if self.current_training:
            self.current_training["status"] = status
            self.current_training.update(kwargs)
            logger.info(f"Trainingsstatus aktualisiert: {status}")
    
    def get_training_status(self) -> Optional[Dict[str, Any]]:
        """
        Gibt den aktuellen Trainingsstatus zurück.
        
        Returns:
            Optional[Dict[str, Any]]: Der Trainingsstatus, falls Training aktiv, sonst None
        """
        return self.current_training
    
    def cancel_training(self):
        """Bricht das aktuelle Training ab."""
        if self.training_active:
            self._update_training_status("cancelled")
            self.training_active = False
            self.current_training = None
            logger.info("Training abgebrochen.")
        else:
            logger.warning("Kein aktives Training zum Abbrechen.")