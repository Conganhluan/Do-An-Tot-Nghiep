import torch.nn as nn
import torch.nn.functional as F
import torch.optim as optim

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

        self.optimizer = optim.SGD(self.parameters(), lr=0.01, momentum=0.5)
        self.batch_size = 1

    def forward(self, x):
        x = self.conv1(x)
        x = self.max_pool2(x)
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