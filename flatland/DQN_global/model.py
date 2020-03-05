import torch.nn as nn
import torch.nn.functional as F

def nn_dimension (x , y , channel_in , channel_out , kernel_size , padding , stride , pooling = True):
    new_x = (x + 2*padding - kernel_size)//stride + 1
    new_y = (y + 2*padding - kernel_size)//stride + 1
    if (pooling):
        new_x = new_x / 2
        new_y = new_y / 2

    return new_x , new_y , channel_out

class QNetwork(nn.Module):
    def __init__(self, width, height , channels , action_size):
        super(QNetwork, self).__init__()
        x , y , channel_in = width , height , channels
        
        self.cl1 = nn.Conv2D (channels , 32 , 3)
        x , y , channel_in = nn_dimension(x , y , channels , 32 , 3 , 0 , 1 , pooling = False)

        self.cl2 = nn.Conv2D (32 , 32 , 3)
        x , y , channel_in = nn_dimension(x , y , 32 , 32 , 3 , 0 , 1)

        self.cl3 = nn.Conv2D (32 , 16 , 3)
        x , y , channel_in = nn_dimension(x , y , 32 , 16 , 3 , 0 , 1)


        self.fc1 = nn.Linear ( x*y*channel_in , 128)
        self.fc2 = nn.Linear (128 , 64)
        self.fc3 = nn.Linear (64 , action_size)

    def forward(self, x):
        
        x = F.relu(self.cl1(x))
        x = F.max_pool2d(F.relu(self.cl2(x)) , 2)
        x = F.max_pool2d(F.relu(self.cl3(x)) , 2)
        x = x.reshape(x.size(0) , -1)

        x = F.relu(self.fc1(x))
        x = F.relu(self.fc2(x))
        x = self.fc3(x)
        return x
