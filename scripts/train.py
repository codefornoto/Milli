#!/usr/bin/env python3
"""Milli文字Transformerの正規PyTorch学習スクリプト。"""
from __future__ import annotations
import argparse, json, math, time
from pathlib import Path
import torch
from torch import nn
import torch.nn.functional as F

class Block(nn.Module):
    def __init__(self,d,h):
        super().__init__(); self.ln1=nn.LayerNorm(d);self.attn=nn.MultiheadAttention(d,h,batch_first=True);self.ln2=nn.LayerNorm(d);self.ff=nn.Sequential(nn.Linear(d,4*d),nn.GELU(),nn.Linear(4*d,d))
    def forward(self,x):
        n=self.ln1(x);t=x.size(1);mask=torch.triu(torch.ones(t,t,device=x.device,dtype=torch.bool),1);x=x+self.attn(n,n,n,attn_mask=mask,need_weights=False)[0];return x+self.ff(self.ln2(x))
class MiniGPT(nn.Module):
    def __init__(self,c):
        super().__init__();d=c['embedding_dim'];self.c=c;self.tok=nn.Embedding(c['vocab_size'],d);self.pos=nn.Embedding(c['context_length'],d);self.blocks=nn.ModuleList([Block(d,c['attention_heads']) for _ in range(c['layers'])]);self.ln=nn.LayerNorm(d);self.head=nn.Linear(d,c['vocab_size'])
    def forward(self,x):
        z=self.tok(x)+self.pos(torch.arange(x.size(1),device=x.device));
        for b in self.blocks:z=b(z)
        return self.head(self.ln(z))
def main():
    p=argparse.ArgumentParser();p.add_argument('--corpus',default='../data/corpus.txt');p.add_argument('--out',default='../model');p.add_argument('--steps',type=int,default=2000);p.add_argument('--batch',type=int,default=24);a=p.parse_args();root=Path(__file__).resolve().parent;text=(root/a.corpus).resolve().read_text(encoding='utf-8');freq={c:text.count(c) for c in set(text)};itos=['<PAD>','<UNK>']+[c for c,_ in sorted(freq.items(),key=lambda x:-x[1])[:1598]];stoi={c:i for i,c in enumerate(itos)};ids=torch.tensor([stoi.get(c,1) for c in text]);split=int(len(ids)*.96);train,val=ids[:split],ids[split:];c={'vocab_size':len(itos),'context_length':64,'embedding_dim':80,'layers':4,'attention_heads':4};device='cuda' if torch.cuda.is_available() else 'cpu';model=MiniGPT(c).to(device);opt=torch.optim.AdamW(model.parameters(),lr=3e-4);ctx=c['context_length']
    def batch(data):
        s=torch.randint(len(data)-ctx-1,(a.batch,));return torch.stack([data[i:i+ctx] for i in s]).to(device),torch.stack([data[i+1:i+ctx+1] for i in s]).to(device)
    out=(root/a.out).resolve();out.mkdir(parents=True,exist_ok=True);loss=0.
    for step in range(1,a.steps+1):
        x,y=batch(train);logits=model(x);l=F.cross_entropy(logits.view(-1,c['vocab_size']),y.view(-1));opt.zero_grad();l.backward();opt.step();loss=float(l)
        if step%50==0:print(step,loss)
        if step in {500,2000,5000} or step==a.steps:
            model.eval();vx,vy=batch(val)
            with torch.no_grad():vl=float(F.cross_entropy(model(vx).view(-1,c['vocab_size']),vy.view(-1)))
            torch.save({'model':model.state_dict(),'config':c,'itos':itos},out/f'model-{step}.pt');model.train();json.dump({'parameters':sum(p.numel() for p in model.parameters()),'training_steps':step,'training_loss':loss,'validation_loss':vl,**c},open(out/f'training_meta-{step}.json','w'),ensure_ascii=False,indent=2)
    (out/'vocab.json').write_text(json.dumps({'itos':itos,'stoi':stoi},ensure_ascii=False,indent=2));(out/'config.json').write_text(json.dumps(c,ensure_ascii=False,indent=2))
if __name__=='__main__':main()
