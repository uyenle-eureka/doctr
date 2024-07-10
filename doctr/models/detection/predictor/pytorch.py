# Copyright (C) 2021-2022, Mindee.

# This program is licensed under the Apache License version 2.
# See LICENSE or go to <https://www.apache.org/licenses/LICENSE-2.0.txt> for full license details.

from typing import Any, List, Dict, Tuple, Union

import numpy as np
import torch
from torch import nn

from doctr.models.preprocessor import PreProcessor

__all__ = ['DetectionPredictor']


class DetectionPredictor(nn.Module):
    """Implements an object able to localize text elements in a document

    Args:
        pre_processor: transform inputs for easier batched model inference
        model: core detection architecture
    """

    def __init__(
        self,
        pre_processor: PreProcessor,
        model: nn.Module,
    ) -> None:

        super().__init__()
        self.pre_processor = pre_processor
        self.model = model.eval()

    @torch.no_grad()
    def forward(
        self,
        pages: List[Union[np.ndarray, torch.Tensor]],
        return_maps: bool = False,
        **kwargs: Any,
    ) -> Union[List[Dict[str, np.ndarray]], Tuple[List[Dict[str, np.ndarray]], List[np.ndarray]]]:

        # Dimension check
        if any(page.ndim != 3 for page in pages):
            raise ValueError("incorrect input shape: all pages are expected to be multi-channel 2D images.")

        processed_batches = self.pre_processor(pages)
        _device = next(self.model.parameters()).device
        predicted_batches = [
            self.model(batch.to(device=_device), return_preds=True, return_model_output=True, **kwargs)  # type:ignore[operator]
            for batch in processed_batches
        ]
        preds = [pred for batch in predicted_batches for pred in batch["preds"]]
        if return_maps:
            seg_maps = [
                pred.permute(1, 2, 0).detach().cpu().numpy() for batch in predicted_batches for pred in batch["out_map"]
            ]
            return preds, seg_maps
        return preds
