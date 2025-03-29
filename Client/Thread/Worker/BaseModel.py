import torch.nn as nn
import torch.nn.functional as F
import torch.optim as optim
from torchvision import models, datasets

class CNNModel_TEST(nn.Module):
    
    def __init__(self, name_dataset):
        
        super().__init__()
        self.conv1 = nn.Conv2d(3,10,kernel_size=5)
        self.max_pool1 = nn.MaxPool2d(kernel_size=2)
        self.conv2 = nn.Conv2d(10,20, kernel_size=5)
        self.max_pool2 = nn.MaxPool2d(kernel_size=2)
        self.conv2_drop = nn.Dropout2d()

        self.fc1 = nn.Linear(20*53*53,50)

        if name_dataset in [datasets.MNIST, datasets.FashionMNIST, datasets.CIFAR10]:    #dataset made from 10 classes
            self.fc2 = nn.Linear(50,10)
        elif name_dataset in [datasets.CIFAR100]:                          #dataset maded from 100 classes
            self.fc2 = nn.Linear(50,100)

        self.optimizer = optim.SGD(self.parameters(), lr=0.01, momentum=0.5)

    def forward(self, x):
        x = self.conv1(x)
        x = self.max_pool1(x)
        x = F.relu(x)
        x = self.conv2(x)
        x = self.max_pool2(x)
        x = F.relu(x)
        x = x.view(-1,20*53*53)
        x = F.relu(self.fc1(x))
        x = F.dropout(x, training=self.training)
        x = self.fc2(x)
        # return F.log_softmax(x, dim = 1) => log_softmax + nll_loss = cross_entropy
        return x

# Please add another model types here
# ...

class Resnet_18(nn.Module):
    def __init__(self, name_dataset):
        super().__init__()
        self.resnet = models.resnet18(pretrained=False)

        if name_dataset in [datasets.MNIST, datasets.FashionMNIST, datasets.CIFAR10]:    #dataset made from 10 classes
            self.resnet.fc = nn.Linear(self.resnet.fc.in_features,10)
        elif name_dataset in [datasets.CIFAR100]:                          #dataset maded from 100 classes
            self.resnet.fc = nn.Linear(self.resnet.fc.in_features,100)      

        self.optimizer = optim.Adam(self.parameters(), lr=0.001)
    
    def forward(self, x):
        self.resnet(x)
        return x
