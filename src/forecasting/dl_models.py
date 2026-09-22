import torch
import torch.nn as nn
import torch.optim as optim
import numpy as np
import pandas as pd
from typing import List, Tuple
from src.utils.logger import get_logger

logger = get_logger("dl_forecasting")

class PyTorchMLP(nn.Module):
    """Deep Multi-Layer Perceptron for Sequence Demand Forecasting."""

    def __init__(self, input_dim: int, hidden_dim: int = 64):
        super(PyTorchMLP, self).__init__()
        self.net = nn.Sequential(
            nn.Linear(input_dim, hidden_dim),
            nn.ReLU(),
            nn.BatchNorm1d(hidden_dim),
            nn.Dropout(0.2),
            nn.Linear(hidden_dim, hidden_dim // 2),
            nn.ReLU(),
            nn.Linear(hidden_dim // 2, 1)
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.net(x)

class DeepForecaster:
    """Deep Learning Neural Forecasting Module (PyTorch)."""

    def __init__(self, feature_cols: List[str], epochs: int = 15, lr: float = 0.005, random_state: int = 42):
        self.feature_cols = feature_cols
        self.epochs = epochs
        self.lr = lr
        self.random_state = random_state
        torch.manual_seed(random_state)
        self.model = None

    def fit(self, X_train: pd.DataFrame, y_train: np.ndarray):
        """Fits PyTorch Deep Neural Network."""
        X_mat = X_train[self.feature_cols].fillna(0.0).values.astype(np.float32)
        y_mat = y_train.astype(np.float32).reshape(-1, 1)

        input_dim = X_mat.shape[1]
        self.model = PyTorchMLP(input_dim=input_dim)
        optimizer = optim.Adam(self.model.parameters(), lr=self.lr)
        criterion = nn.MSELoss()

        dataset = torch.utils.data.TensorDataset(torch.tensor(X_mat), torch.tensor(y_mat))
        loader = torch.utils.data.DataLoader(dataset, batch_size=256, shuffle=True)

        self.model.train()
        for epoch in range(self.epochs):
            for batch_x, batch_y in loader:
                optimizer.zero_grad()
                out = self.model(batch_x)
                loss = criterion(out, batch_y)
                loss.backward()
                optimizer.step()

        logger.info(f"Trained PyTorch Deep Neural Forecasting Model ({self.epochs} epochs).")

    def predict(self, X_test: pd.DataFrame) -> np.ndarray:
        """Generates predictions with Deep Neural Model."""
        if self.model is None:
            raise ValueError("DeepForecaster model has not been trained yet.")
        self.model.eval()
        X_mat = X_test[self.feature_cols].fillna(0.0).values.astype(np.float32)
        with torch.no_grad():
            preds = self.model(torch.tensor(X_mat)).numpy().flatten()
        return np.maximum(0.0, preds)
