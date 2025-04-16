import torch.nn as nn
import torch.nn.functional as F
from torchvision import models
import torch.optim as optim
from torch.nn import CrossEntropyLoss


class CNNModel_MNIST(nn.Module):
    
    def __init__(self):
        
        super().__init__()
        self.conv1 = nn.Conv2d(1,10,kernel_size=5)
        self.max_pool1 = nn.MaxPool2d(kernel_size=2)
        self.conv2 = nn.Conv2d(10,20, kernel_size=5)
        self.max_pool2 = nn.MaxPool2d(kernel_size=2)
        self.conv2_drop = nn.Dropout2d()
        self.fc1 = nn.Linear(320,50)
        self.fc2 = nn.Linear(50,10)

    def forward(self, x):
        x = self.conv1(x)
        x = self.max_pool1(x)  # Fixed: Using max_pool1 instead of max_pool2
        x = F.relu(x)
        x = self.conv2(x)
        x = self.max_pool2(x)
        x = F.relu(x)
        x = x.view(-1,320)
        x = F.relu(self.fc1(x))
        x = F.dropout(x, training=self.training)
        x = self.fc2(x)
        return F.log_softmax(x, dim = 1) 

# Please add another model types here
# ...

# class CNNModel_MNIST(nn.Module):
    
#     def __init__(self):
#         super().__init__()
#         self.resnet = models.resnet18(weights = None)
#         self.resnet.conv1 = nn.Conv2d(in_channels=1, out_channels = 64, kernel_size=7, stride=2, padding=3, bias=False)
#         #dataset made from 10 classes
#         self.resnet.fc = nn.Linear(self.resnet.fc.in_features,10)
#         self.optimizer = optim.Adam(self.parameters(), lr=0.001)
#         self.loss = CrossEntropyLoss()
    
#     def forward(self, x):
#         return self.resnet(x)