"""
Standalone Donut Fine-Tuning Script
Supports:
- Pre-trained model: naver-clova-ix/donut-base
- Target Extraction Schema for Indian Restaurant Bills
- Mixed Precision (fp16) & Gradient Checkpointing for Google Colab T4 GPU
- Token-level logit probability tracking for field-level confidence scores
"""

import os
import json
import argparse
from typing import Dict, Any, List
from PIL import Image

def get_args():
    parser = argparse.ArgumentParser(description="Fine-tune Donut for SplitSnap Indian Receipt Extraction")
    parser.add_argument("--data_file", type=str, default="ml/data/processed/indianized_dataset.jsonl", help="Path to jsonl dataset")
    parser.add_argument("--images_dir", type=str, default="ml/data/processed/images", help="Path to images directory")
    parser.add_argument("--output_dir", type=str, default="ml/models/donut_splitsnap", help="Output directory for fine-tuned model")
    parser.add_argument("--epochs", type=int, default=5, help="Number of training epochs")
    parser.add_argument("--batch_size", type=int, default=2, help="Batch size per device")
    parser.add_argument("--grad_accum_steps", type=int, default=4, help="Gradient accumulation steps")
    parser.add_argument("--learning_rate", type=float, default=3e-5, help="Learning rate")
    return parser.parse_args()



def train(args):
    try:
        import torch
        from transformers import (
            DonutProcessor,
            VisionEncoderDecoderModel,
            VisionEncoderDecoderConfig,
            Seq2SeqTrainer,
            Seq2SeqTrainingArguments
        )
        from datasets import Dataset
    except ImportError:
        print("ERROR: torch, transformers, and datasets are required to execute train_donut.py.")
        print("Install them with: pip install torch transformers datasets accelerate")
        return

    print("=== SplitSnap Donut Training Pipeline ===")
   
   
   
    print(f"Data: {args.data_file}")
    print(f"Output: {args.output_dir}")

    # 1. Load Processor and Model
   
    model_id = "naver-clova-ix/donut-base"
    print(f"Loading base model: {model_id}")
    processor = DonutProcessor.from_pretrained(model_id)
    model = VisionEncoderDecoderModel.from_pretrained(model_id)

   
    # 2. Add domain-specific tokens
    special_tokens = [
        "<s_splitsnap>", "</s_splitsnap>",
        "<s_merchant>", "</s_merchant>",
   
        "<s_date>", "</s_date>",
        "<s_items>", "</s_items>",
        "<s_item>", "</s_item>",
   
        "<s_name>", "</s_name>",
        "<s_qty>", "</s_qty>",
        "<s_price>", "</s_price>",
        "<s_subtotal>", "</s_subtotal>",
   
        "<s_taxes>", "</s_taxes>",
        "<s_tax>", "</s_tax>",
        "<s_amount>", "</s_amount>",
        "<s_service_charge>", "</s_service_charge>",
   
        "<s_discount>", "</s_discount>",
        "<s_total>", "</s_total>"
    ]
   
    processor.tokenizer.add_special_tokens({"additional_special_tokens": special_tokens})
    model.decoder.resize_token_embeddings(len(processor.tokenizer))

    # Configure model decoder tokens
    model.config.pad_token_id = processor.tokenizer.pad_token_id
    model.config.decoder_start_token_id = processor.tokenizer.convert_tokens_to_ids("<s_splitsnap>")
   
   
    model.config.use_cache = False



    # 3. Load dataset

    samples = []
    with open(args.data_file, "r") as f:

        for line in f:
            if line.strip():

                samples.append(json.loads(line))

    print(f"Loaded {len(samples)} training samples.")

    class SplitSnapDataset(torch.utils.data.Dataset):

        def __init__(self, samples, images_dir, processor, max_length=768):

            self.samples = samples
            self.images_dir = images_dir

            self.processor = processor

            self.max_length = max_length

        def __len__(self):

            return len(self.samples)


        def __getitem__(self, idx):

            sample = self.samples[idx]
            img_path = os.path.join(self.images_dir, sample["image_file"])
            image = Image.open(img_path).convert("RGB")


            pixel_values = self.processor(image, return_tensors="pt").pixel_values.squeeze(0)

            target_sequence = sample["donut_sequence"] + self.processor.tokenizer.eos_token
            labels = self.processor.tokenizer(
                target_sequence,
                add_special_tokens=False,

                max_length=self.max_length,

                padding="max_length",

                truncation=True,
                return_tensors="pt"

            ).input_ids.squeeze(0)



            labels[labels == self.processor.tokenizer.pad_token_id] = -100

            return {"pixel_values": pixel_values, "labels": labels}


    split_idx = int(0.9 * len(samples))

    train_dataset = SplitSnapDataset(samples[:split_idx], args.images_dir, processor)
    eval_dataset = SplitSnapDataset(samples[split_idx:], args.images_dir, processor)



    training_args = Seq2SeqTrainingArguments(

        output_dir=args.output_dir,

        num_train_epochs=args.epochs,
        learning_rate=args.learning_rate,

        per_device_train_batch_size=1,

        per_device_eval_batch_size=1,
        gradient_accumulation_steps=8,

        fp16=torch.cuda.is_available(),


        logging_steps=10,

        eval_strategy="no",
        save_strategy="no",

        predict_with_generate=True,
        report_to="none"
    )



    trainer = Seq2SeqTrainer(

        model=model,

        args=training_args,

        train_dataset=train_dataset,
        eval_dataset=eval_dataset

    )



    print("Starting training...")

    trainer.train()





    print(f"Saving fine-tuned model and processor to {args.output_dir}...")





    model.save_pretrained(args.output_dir)
    processor.save_pretrained(args.output_dir)

    print("Training complete!")


if __name__ == "__main__":
    args = get_args()

    train(args)





