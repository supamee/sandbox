
import torch
import timeit
import torchvision.models as models
import numpy as np
from time import time
from torch2trt import torch2trt

import pickle

from torch2trt.torch2trt import *
from torch2trt.module_test import add_module_test

@tensorrt_converter('torch.Tensor.rsqrt')
@tensorrt_converter('torch.nn.functional.rsqrt')
def convert_rsqrt(ctx):
    input = ctx.method_args[0]
    input_trt = add_missing_trt_tensors(ctx.network, [input])[0]
    output = ctx.method_return
    y = ctx.network.add_unary(input_trt, trt.UnaryOperation.SQRT).get_output(0)  # y = sqrt(x)
    z = ctx.network.add_unary(y, trt.UnaryOperation.RECIP).get_output(0)  # z = 1.0 / x
    output._trt = z

def inference_test():
    device = torch.device('cuda:0')

    # Create model and input.
    # model = models.resnet50(pretrained=True).half()
    # model = models.detection.ssd300_vgg16(pretrained=True).backbone.half() # work
    # model = models.detection.fasterrcnn_resnet50_fpn(pretrained=True).half()# doesn't work
    # model = models.detection.fasterrcnn_mobilenet_v3_large_fpn(pretrained=True).half()# doesn't work
    model = models.detection.retinanet_resnet50_fpn(pretrained=True).backbone.half()# doesn't work


    tmp = (np.random.standard_normal([1, 3, 224, 224]) * 255).astype(np.uint8)  
    # tmp = (np.random.standard_normal([1, 3, 416, 416]) * 255).astype(np.uint8)  #mobilenet_v2

    # move them to the device 
    model.eval()
    model.to(device)   
    img = torch.from_numpy(tmp.astype(np.float16)).to(device)

    # tic = time()
    # for i in range(100):
    #     x=model(img)
    # print("test: ", time()-tic)
    # print(x)

    # convert to TensorRT feeding sample data as input
    print("about to convert")
    start_convert=time()
    model_trt = torch2trt(model, [img], fp16_mode=True)
    print("done convert, it took",time()-start_convert)
    import pdb; pdb.set_trace()
    def infer():
        
        with torch.no_grad():
            before = time()
            # outs = model(img)
            outs = model_trt(img)
            infer_time = time() - before
            print(type(outs),outs.device)
        return infer_time

    print("Running warming up iterations..")
    for i in range(0, 100):
        infer()

    total_times = timeit.repeat(stmt=infer, repeat=1, number=500)    
    print("Timeit.repeat: ", total_times)
    print("FPS: ", 500 / np.array(total_times).mean())

inference_test()

