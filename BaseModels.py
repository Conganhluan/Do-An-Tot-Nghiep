import torch
import torch.nn as nn
import torch.nn.functional as F

class CNNModel(nn.Module):
    def __init__(self):
        super(CNNModel, self).__init__()
        self.conv1 = nn.Conv2d(1, 32, kernel_size=3, stride=1, padding=1)
        self.conv2 = nn.Conv2d(32, 64, kernel_size=3, stride=1, padding=1)
        self.pool = nn.MaxPool2d(kernel_size=2, stride=2)
        self.fc1 = nn.Linear(64 * 7 * 7, 128)
        self.fc2 = nn.Linear(128, 10)

    def forward(self, x):
        x = self.pool(F.relu(self.conv1(x)))  # Output: (batch_size, 32, 14, 14)
        x = self.pool(F.relu(self.conv2(x)))  # Output: (batch_size, 64, 7, 7)
        x = torch.flatten(x, 1)               # Flatten to (batch_size, 64*7*7)
        x = F.relu(self.fc1(x))               # Fully connected layer
        x = self.fc2(x)                       # Output layer
        return x