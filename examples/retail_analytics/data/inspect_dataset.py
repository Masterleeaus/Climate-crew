from datasets import load_dataset_builder, load_dataset

dataset_name = "G11/climate_adaptation_abstracts"
try:
    ds_builder = load_dataset_builder(dataset_name)
    print(f"Builder found for {dataset_name}")
    print(f"Features: {ds_builder.info.features}")
    
    # Try loading a sample
    ds = load_dataset(dataset_name, split="train", streaming=True)
    sample = next(iter(ds))
    print("Sample row keys:", sample.keys())
except Exception as e:
    print(f"Error inspecting {dataset_name}: {e}")
