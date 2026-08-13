#!/usr/bin/env python3
"""PyTorch checkpointをONNXへ変換する。train.pyと同じディレクトリで使う。"""
import argparse, json, torch
from pathlib import Path
from train import MiniGPT
p=argparse.ArgumentParser();p.add_argument('checkpoint');p.add_argument('--out',default='../model/model.onnx');a=p.parse_args();ck=torch.load(a.checkpoint,map_location='cpu');model=MiniGPT(ck['config']);model.load_state_dict(ck['model']);model.eval();ctx=ck['config']['context_length'];dummy=torch.zeros((1,ctx),dtype=torch.long);torch.onnx.export(model,dummy,(Path(__file__).parent/a.out).resolve(),input_names=['input_ids'],output_names=['logits'],dynamic_axes={'input_ids':{0:'batch',1:'sequence'},'logits':{0:'batch',1:'sequence'}},opset_version=17)
