import torch
from torch.utils.data import DataLoader, TensorDataset, Subset
import torch.nn.functional as F
from torch.nn.utils import parameters_to_vector, vector_to_parameters
from BaseModel import *
import torchvision
from tqdm import tqdm
from Thread.Worker.Helper import Helper
class Trainer:

    def __init__(self, model_type: type):
        self.local_model : CNNModel_MNIST = model_type()
        self.dataset_type = model_type.__name__.split('_')[-1]

    def set_dataset_ID(self, ID: int):
        self.ID = ID

        # Dataset
            # Root dataset
        self.root_dataset : type = getattr(torchvision.datasets, self.dataset_type)
        self.root_train_data : torchvision.datasets.MNIST = self.root_dataset(root="Thread/Worker/Data", train=True, download=True, transform=torchvision.transforms.Compose([torchvision.transforms.ToTensor()]))
        self.root_test_data : torchvision.datasets.MNIST = self.root_dataset(root="Thread/Worker/Data", train=False, download=True, transform=torchvision.transforms.Compose([torchvision.transforms.ToTensor()]))
            # Self dataset
        self.data_num = self.root_train_data.__len__() // int(Helper.get_env_variable('ATTEND_CLIENTS'))
        self.self_train_data = Subset(self.root_train_data, range(self.ID * self.data_num, (self.ID + 1) * self.data_num))
        self.self_test_data = Subset(self.root_test_data, range(self.ID * self.data_num, (self.ID + 1) * self.data_num))

    def load_parameters(self, parameters: list):
        tensor = torch.tensor(parameters, requires_grad=True)
        vector_to_parameters(tensor, self.local_model._parameters)

    def get_parameters(self) -> list:
        return parameters_to_vector(self.local_model.parameters()).detach().numpy().tolist()

    def __get_data__(self, data: Subset) -> TensorDataset:
        
        if self.root_dataset == torchvision.datasets.MNIST:
            origin_data = torch.stack([data.dataset[idx][0] for idx in data.indices])
            target_label = torch.tensor([data.dataset[idx][1] for idx in data.indices])
            return TensorDataset(origin_data, target_label)
    
        # Please input here any another root_dataset type (cifar10, cifar100, etc.)
        # elif self.root_dataset == torchvision.datasets.CIFAR10:
        #     pass

        else:
            raise Exception("There is no data available to get!")
        
    def __get_train_data__(self) -> TensorDataset:
        return self.__get_data__(self.self_train_data)
    
    def __get_test_data__(self) -> TensorDataset:
        return self.__get_data__(self.self_test_data)

    @Helper.timing
    def train(self, data_loader: DataLoader):
        
        for data, target in tqdm(data_loader, unit="batch", leave=False):
            self.local_model.optimizer.zero_grad()
            output = self.local_model(data)
            loss = F.nll_loss(output, target)
            loss.backward()
            self.local_model.optimizer.step()
    
    @torch.no_grad
    def test(self, data_loader: DataLoader, epoch_idx: int):
        
        test_loss = 0
        correct = 0

        for data, target in tqdm(data_loader, unit="batch", leave=False):
            output = self.local_model(data)
            test_loss += F.nll_loss(output, target, reduction="sum").item()
            pred = output.data.max(1, keepdim = True)[1]
            correct += pred.eq(target.view_as(pred)).long().cpu().sum()
        test_loss /= len(data_loader.dataset)
        print('Epoch {} result: Average loss: {:.4f}, Accuracy: {}/{} ({:.0f}%)'.format(
            epoch_idx, test_loss, correct, len(data_loader.dataset),
            100. * correct / len(data_loader.dataset)))

    def train_model(self):

        epoch_idx = 0
        while True:
            train_loader = DataLoader(self.__get_train_data__(), batch_size = self.local_model.batch_size)
            test_loader = DataLoader(self.__get_test_data__())

            self.local_model.train()
            self.train(train_loader)
            epoch_idx += 1
            self.local_model.eval()
            self.test(test_loader, epoch_idx)
            
    
# Unit test
if __name__ == "__main__":
    trainer = Trainer(CNNModel_MNIST)
    trainer.set_dataset_ID(0)
    trainer.train_model()