import os
from torchvision import datasets, transforms
from torch.utils.data import random_split
import torch

class Splitter:
  def __init__(self, dataset_name):
      self.dataset_name = dataset_name
      self.output_dir = f"./{dataset_name.lower()}_splits"

  def split_dataset(self, train_split=200, test_split=1):
    # Ensure output directory exists
    os.makedirs(self.output_dir, exist_ok=True)

    # Define dataset-specific transformations
    transform = transforms.Compose([transforms.ToTensor()])

    # Load the specified dataset
    if self.dataset_name == "MNIST":
        train_dataset = datasets.MNIST(root=self.output_dir, train=True, download=True, transform=transform)
        test_dataset = datasets.MNIST(root=self.output_dir, train=False, download=True, transform=transform)
    elif self.dataset_name == "CIFAR10":
        train_dataset = datasets.CIFAR10(root=self.output_dir, train=True, download=True, transform=transform)
        test_dataset = datasets.CIFAR10(root=self.output_dir, train=False, download=True, transform=transform)
    elif self.dataset_name == "CIFAR100":
        train_dataset = datasets.CIFAR100(root=self.output_dir, train=True, download=True, transform=transform)
        test_dataset = datasets.CIFAR100(root=self.output_dir, train=False, download=True, transform=transform)
    else:
        raise ValueError(f"Unsupported dataset: {self.dataset_name}")

    # Calculate split sizes
    train_size = len(train_dataset) // train_split
    test_size = len(test_dataset) // test_split

    # Split training data
    train_splits = random_split(train_dataset, [train_size] * train_split)
    for i, split in enumerate(train_splits):
        torch.save(split, os.path.join(self.output_dir, f"{self.dataset_name.lower()}_train_split_{i}.pt"))

    # Split testing data
    test_splits = random_split(test_dataset, [test_size] * test_split)
    for i, split in enumerate(test_splits):
        torch.save(split, os.path.join(self.output_dir, f"{self.dataset_name.lower()}_test_split_{i}.pt"))

    print(f"{self.dataset_name} dataset split into {train_split} training parts and {test_split} testing parts.")

print(__name__)
if __name__ == "__main__":
  splitter = Splitter("MNIST")
  splitter.split_dataset()
  splitter = Splitter("CIFAR10")
  splitter.split_dataset()
  splitter = Splitter("CIFAR100")
  splitter.split_dataset()

