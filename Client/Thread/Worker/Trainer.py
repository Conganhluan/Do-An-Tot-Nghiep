import torch, numpy
from torch.utils.data import DataLoader, TensorDataset, Subset
import torch.nn.functional as F
from torch.nn.utils import parameters_to_vector, vector_to_parameters
from Thread.Worker.BaseModel import *
import torchvision, torch.optim as optim
from tqdm import tqdm
from Thread.Worker.Helper import Helper

class Trainer:

    def __init__(self, model_type: type):
        self.local_model : CNNModel_MNIST = model_type()
        self.dataset_type = model_type.__name__.split('_')[-1]
        self.batch_size = 64
        self.epoch_num = 3
        self.optimizer = optim.SGD(self.local_model.parameters(), lr=0.01, momentum=0.5)
        self.get_parameters()

    def set_dataset_ID(self, ID: int, round_number: int):
        self.ID = ID

        # Dataset
            
            # Root dataset
        self.root_dataset : type = getattr(torchvision.datasets, self.dataset_type)
        self.root_train_data : torchvision.datasets.MNIST = self.root_dataset(root="Thread/Worker/Data", train=True, download=False, transform=torchvision.transforms.Compose([torchvision.transforms.ToTensor()]))
        self.root_test_data : torchvision.datasets.MNIST = self.root_dataset(root="Thread/Worker/Data", train=False, download=False, transform=torchvision.transforms.Compose([torchvision.transforms.ToTensor()]))
            
            # Self dataset
        ATTEND_CLIENTS = int(Helper.get_env_variable('ATTEND_CLIENTS'))
        # self.data_num = self.root_train_data.__len__() // ATTEND_CLIENTS
        # self.self_train_data = Subset(self.root_train_data, range(self.ID * self.data_num, (self.ID + 1) * self.data_num))

        self.data_num = self.root_train_data.__len__() // 100
        self.self_train_data = Subset(self.root_train_data, range((round_number * ATTEND_CLIENTS + self.ID) * self.data_num, (round_number * ATTEND_CLIENTS + self.ID + 1) * self.data_num))

        # self.test_data_num = self.root_test_data.__len__() // ATTEND_CLIENTS
        # self.self_test_data = Subset(self.root_test_data, range(self.ID * self.test_data_num, (self.ID + 1) * self.test_data_num))

        self.test_data_num = self.root_test_data.__len__() // 100
        self.self_test_data = Subset(self.root_test_data, range((round_number * ATTEND_CLIENTS + self.ID) * self.test_data_num, (round_number * ATTEND_CLIENTS + self.ID + 1) * self.test_data_num))

    def load_parameters(self, parameters: numpy.ndarray[numpy.float32], round_ID: int):
        tensor = torch.tensor(parameters, dtype=torch.float32, requires_grad=True)
        torch.save(self.local_model, f"Thread/Worker/Data/Models/{round_ID}_old.pth")
        vector_to_parameters(tensor, self.local_model.parameters())
        torch.save(self.local_model, f"Thread/Worker/Data/Models/{round_ID}_new.pth")

    def get_parameters(self) -> numpy.ndarray[numpy.float32]:
        return parameters_to_vector(self.local_model.parameters()).detach().numpy()

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
        
        for data, target in tqdm(data_loader, unit=" data", leave=False):
            self.optimizer.zero_grad()
            output = self.local_model(data)
            loss = F.nll_loss(output, target)
            loss.backward()
            self.optimizer.step()
    
    @torch.no_grad
    def test(self, data_loader: DataLoader, epoch_idx: int) -> float:
        
        test_loss = 0
        correct = 0

        for data, target in tqdm(data_loader, unit=" data", leave=False):
            output = self.local_model(data)
            test_loss += F.nll_loss(output, target, reduction="sum").item()
            pred = output.data.max(1, keepdim = True)[1]
            correct += pred.eq(target.view_as(pred)).long().cpu().sum()
        test_loss /= len(data_loader.dataset)
        accuracy_rate = 100. * correct / len(data_loader.dataset)
        print('Epoch {} result: Average loss: {:.4f}, Accuracy: {}/{} ({:.0f}%)'.format(
            epoch_idx, test_loss, correct, len(data_loader.dataset), accuracy_rate))
        
        return accuracy_rate
    
    @torch.no_grad
    def self_evaluate(self) -> float:

        test_loss = 0
        correct = 0
        data_loader = DataLoader(self.__get_data__(self.self_test_data))

        for data, target in tqdm(data_loader, unit=" data", leave=False):
            output = self.local_model(data)
            test_loss += F.nll_loss(output, target, reduction="sum").item()
            pred = output.data.max(1, keepdim = True)[1]
            correct += pred.eq(target.view_as(pred)).long().cpu().sum()
        test_loss /= len(data_loader.dataset)
        accuracy_rate = 100. * correct / len(data_loader.dataset)
        print('Round result: Average loss: {:.4f}, Accuracy: {}/{} ({:.0f}%)'.format(
            test_loss, correct, len(data_loader.dataset), accuracy_rate))

        del self.self_test_data
        del self.self_train_data

        return accuracy_rate

    @torch.no_grad
    def total_evaluate(self):

        test_loss = 0
        correct = 0
        data_loader = DataLoader(self.__get_data__(Subset(self.root_test_data, range(len(self.root_test_data)))))

        for data, target in tqdm(data_loader, unit=" data", leave=False):
            output = self.local_model(data)
            test_loss += F.nll_loss(output, target, reduction="sum").item()
            pred = output.data.max(1, keepdim = True)[1]
            correct += pred.eq(target.view_as(pred)).long().cpu().sum()
        test_loss /= len(data_loader.dataset)
        accuracy_rate = 100. * correct / len(data_loader.dataset)
        print('Round result: Average loss: {:.4f}, Accuracy: {}/{} ({:.0f}%)'.format(
            test_loss, correct, len(data_loader.dataset), accuracy_rate))

        del self.root_test_data
        del self.root_train_data

    def train_model(self):

        train_loader = DataLoader(self.__get_train_data__(), batch_size = self.batch_size)
        test_loader = DataLoader(self.__get_test_data__())
        
        for epoch_idx in range(self.epoch_num):  
            self.local_model.train()
            self.train(train_loader)
            epoch_idx += 1
            self.local_model.eval()
            self.test(test_loader, epoch_idx)

    def test_model(self):
        test_loader = DataLoader(self.__get_test_data__())
        self.local_model.eval()
        self.test(test_loader, epoch_idx=0)