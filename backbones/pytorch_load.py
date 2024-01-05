import torch
from torch import nn
from .layer_factory import get_basic_layer, parse_expr, build_gsf
import torch.utils.model_zoo as model_zoo
import yaml

class BNInception(nn.Module):
    def __init__(self, model_path='backbones/bn_inception.yaml', num_classes=101,
                 weight_url='https://yjxiong.blob.core.windows.net/models/bn_inception-9f5701afb96c8044.pth',
                 gen_vis=False, save_feats=False):
        super(BNInception, self).__init__()
        strict_load = True
        if gen_vis or save_feats:
            model_path = model_path.replace('.yaml', '_vis.yaml')
            strict_load = False
        manifest = yaml.safe_load(open(model_path))

        layers = manifest['layers']

        self._channel_dict = dict()

        self._op_list = list()
        for l in layers:
            out_var, op, in_var = parse_expr(l['expr'])
            if op != 'Concat':
                id, out_name, module, out_channel, in_name = get_basic_layer(l,
                                                                3 if len(self._channel_dict) == 0 else self._channel_dict[in_var[0]],
                                                                             conv_bias=True)

                self._channel_dict[out_name] = out_channel
                setattr(self, id, module)
                self._op_list.append((id, op, out_name, in_name))
            else:
                self._op_list.append((id, op, out_var[0], in_var))
                channel = sum([self._channel_dict[x] for x in in_var])
                self._channel_dict[out_var[0]] = channel

        state_dict = torch.utils.model_zoo.load_url(weight_url)
        for k, v in state_dict.items():
            state_dict[k] = torch.squeeze(v, dim=0)
        self.load_state_dict(state_dict, strict=strict_load)


    def forward(self, input):
        data_dict = dict()
        data_dict[self._op_list[0][-1]] = input

        def get_hook(name):

            def hook(m, grad_in, grad_out):
                print(name, grad_out[0].data.abs().mean())

            return hook
        for op in self._op_list:
            if op[1] != 'Concat' and op[1] != 'InnerProduct':
                data_dict[op[2]] = getattr(self, op[0])(data_dict[op[-1]])
                # getattr(self, op[0]).register_backward_hook(get_hook(op[0]))
                # print(data_dict[op[2]].size())
            elif op[1] == 'InnerProduct':
                x = data_dict[op[-1]]
                data_dict[op[2]] = getattr(self, op[0])(x.view(x.size(0), -1))
            else:
                try:
                    data_dict[op[2]] = torch.cat(tuple(data_dict[x] for x in op[-1]), 1)
                except:
                    for x in op[-1]:
                        print(x,data_dict[x].size())
                    raise
        return data_dict[self._op_list[-1][2]]

class BNInception_gsf(nn.Module):
    def __init__(self, model_path='backbones/bn_inception_gsf.yaml', num_classes=101,
                 weight_url='https://yjxiong.blob.core.windows.net/models/bn_inception-9f5701afb96c8044.pth',
                 num_segments=8, gsf_ch_ratio=100):
        super(BNInception_gsf, self).__init__()

        manifest = yaml.safe_load(open(model_path))

        layers = manifest['layers']

        self._channel_dict = dict()

        self._op_list = list()
        gsf_cnt = 0
        for l in layers:
            out_var, op, in_var = parse_expr(l['expr'])
            if op != 'Concat':
                if op == 'gsf':
                    gsf_cnt += 1
                    id, out_name, module, out_channel, in_name = build_gsf(l,  num_segments=num_segments,
                                                                           gsf_ch_ratio=gsf_ch_ratio)

                    self._channel_dict[out_name] = out_channel
                    setattr(self, id, module)
                    self._op_list.append((id, op, out_name, in_name))
                else:
                    
                    id, out_name, module, out_channel, in_name = get_basic_layer(l,
                                                                                 3 if len(
                                                                                     self._channel_dict) == 0 else
                                                                                 self._channel_dict[in_var[0]],
                                                                                 conv_bias=True)
                    self._channel_dict[out_name] = out_channel
                    setattr(self, id, module)
                    self._op_list.append((id, op, out_name, in_name))
            else:
                self._op_list.append((id, op, out_var[0], in_var))
                channel = sum([self._channel_dict[x] for x in in_var])
                self._channel_dict[out_var[0]] = channel
        
        state_dict = torch.utils.model_zoo.load_url(weight_url)
        for k, v in state_dict.items():
            state_dict[k] = torch.squeeze(v, dim=0)
        self.load_state_dict(state_dict, strict=False)
        print('No. of GSF modules = {}'.format(gsf_cnt))

    def forward(self, input):
        data_dict = dict()
        data_dict[self._op_list[0][-1]] = input

        def get_hook(name):

            def hook(m, grad_in, grad_out):
                print(name, grad_out[0].data.abs().mean())

            return hook
        for op in self._op_list:
            if op[1] != 'Concat' and op[1] != 'InnerProduct':
                data_dict[op[2]] = getattr(self, op[0])(data_dict[op[-1]])

            elif op[1] == 'InnerProduct':
                x = data_dict[op[-1]]
                data_dict[op[2]] = getattr(self, op[0])(x.view(x.size(0), -1))
            else:
                try:
                    data_dict[op[2]] = torch.cat(tuple(data_dict[x] for x in op[-1]), 1)
                except:
                    for x in op[-1]:
                        print(x,data_dict[x].size())
                    raise
        return data_dict[self._op_list[-1][2]]


# ADDED
class BNInception_kinetics_gsf(nn.Module):
    def __init__(self, model_path='backbones/bn_inception_gsf.yaml', num_classes=101,
                 weight_url='https://yjxiong.blob.core.windows.net/models/bn_inception-9f5701afb96c8044.pth',
                 num_segments=8, gsf_ch_ratio=100):
        super(BNInception_kinetics_gsf, self).__init__()

        print("Loading BNInception_kinetics_gsf with kinetics! \n")
        manifest = yaml.safe_load(open(model_path))

        layers = manifest['layers']

        self._channel_dict = dict()

        self._op_list = list()
        gsf_cnt = 0
        for l in layers:
            out_var, op, in_var = parse_expr(l['expr'])
            if op != 'Concat':
                if op == 'gsf':
                    gsf_cnt += 1
                    id, out_name, module, out_channel, in_name = build_gsf(l,  num_segments=num_segments,
                                                                           gsf_ch_ratio=gsf_ch_ratio)

                    self._channel_dict[out_name] = out_channel
                    setattr(self, id, module)
                    self._op_list.append((id, op, out_name, in_name))
                else:
                    
                    id, out_name, module, out_channel, in_name = get_basic_layer(l,
                                                                                 3 if len(
                                                                                     self._channel_dict) == 0 else
                                                                                 self._channel_dict[in_var[0]],
                                                                                 conv_bias=True)
                    self._channel_dict[out_name] = out_channel
                    setattr(self, id, module)
                    self._op_list.append((id, op, out_name, in_name))
            else:
                self._op_list.append((id, op, out_var[0], in_var))
                channel = sum([self._channel_dict[x] for x in in_var])
                self._channel_dict[out_var[0]] = channel
        
        state_dict = torch.utils.model_zoo.load_url(weight_url)
        state_dict = state_dict['state_dict']
        for k, v in state_dict.items():
            state_dict[k] = torch.squeeze(v, dim=0)
        self.load_state_dict(state_dict, strict=False)
        print('No. of GSF modules = {}'.format(gsf_cnt))

    def forward(self, input):
        data_dict = dict()
        data_dict[self._op_list[0][-1]] = input

        def get_hook(name):

            def hook(m, grad_in, grad_out):
                print(name, grad_out[0].data.abs().mean())

            return hook
        for op in self._op_list:
            if op[1] != 'Concat' and op[1] != 'InnerProduct':
                data_dict[op[2]] = getattr(self, op[0])(data_dict[op[-1]])

            elif op[1] == 'InnerProduct':
                x = data_dict[op[-1]]
                data_dict[op[2]] = getattr(self, op[0])(x.view(x.size(0), -1))
            else:
                try:
                    data_dict[op[2]] = torch.cat(tuple(data_dict[x] for x in op[-1]), 1)
                except:
                    for x in op[-1]:
                        print(x,data_dict[x].size())
                    raise
        return data_dict[self._op_list[-1][2]]


class InceptionV3(BNInception):
    def __init__(self, model_path='backbones/inceptionv3.yaml', num_classes=101,
                 weight_url='https://yjxiong.blob.core.windows.net/models/inceptionv3-cuhk-0e09b300b493bc74c.pth'):
        super(InceptionV3, self).__init__(model_path=model_path, weight_url=weight_url, num_classes=num_classes)

# https://yjxiong.blob.core.windows.net/models/inceptionv3-cuhk-0e09b300b493bc74c.pth
class InceptionV3_gsf(BNInception_gsf):
    def __init__(self, model_path='backbones/inceptionv3_gsf.yaml', num_classes=101,
                 weight_url='https://yjxiong.blob.core.windows.net/models/inceptionv3-cuhk-0e09b300b493bc74c.pth',
                 num_segments=8, gsf_ch_ratio=100):
        super(InceptionV3_gsf, self).__init__(model_path=model_path, weight_url=weight_url,
                                              num_classes=num_classes, num_segments=num_segments,
                                              gsf_ch_ratio=gsf_ch_ratio)
        
# InceptionV3 - Kinetics
class InceptionV3_kinetics_gsf(BNInception_kinetics_gsf):
    def __init__(self, model_path='backbones/inceptionv3_gsf.yaml', num_classes=101,
                 weight_url='https://yjxiong.blob.core.windows.net/ssn-models/inceptionv3_rgb_kinetics_init-c42e70a05e22.pth',
                 num_segments=8, gsf_ch_ratio=100):
        super(InceptionV3_kinetics_gsf, self).__init__(model_path=model_path, weight_url=weight_url,
                                              num_classes=num_classes, num_segments=num_segments,
                                              gsf_ch_ratio=gsf_ch_ratio)

"""
Checkpoint from:
    https://github.com/epic-kitchens/epic-kitchens-55-action-models/blob/master/archs/bn_inception.py
Link:
    https://www.dropbox.com/s/gx4u7itoyygix0c/BNInceptionKinetics-47f0695e.pth?dl=1

From same of the one present before:
# https://yjxiong.blob.core.windows.net/ssn-models/inceptionv3_rgb_kinetics_init-c42e70a05e22.pth
"""