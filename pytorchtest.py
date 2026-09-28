from torchvision import datasets, transforms
from torch.utils.data import DataLoader

transform = transforms.Compose([
    transforms.Grayscale(),        # already grayscale but safe
    transforms.Resize((64, 64)),
    transforms.ToTensor(),
])

dataset = datasets.ImageFolder(
    root="Z:/MTGSymbolDataset",
    transform=transform
)

dataloader = DataLoader(dataset, batch_size=32, shuffle=True)