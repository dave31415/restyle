import torchvision.models as tv_models
import torch
from PIL import Image
from io import BytesIO
import requests
from restyle.utils import image_to_tensor


def get_cnn_model(device):
    # Neural network used.
    cnn = tv_models.vgg19(pretrained=True).features.to(device).eval()
    # Normalization mean and standard deviation.
    cnn_normalization_mean = torch.tensor([0.485, 0.456, 0.406]).to(device)
    cnn_normalization_std = torch.tensor([0.229, 0.224, 0.225]).to(device)
    return cnn, cnn_normalization_mean, cnn_normalization_std


def open_image(url):
    if url.startswith("http"):
        return Image.open(BytesIO(requests.get(url).content)).convert('RGB')
    else:
        return Image.open(url).convert('RGB')


def load_content_image(params):
    content_image = open_image(params['content_image_path'])
    original_content_image_size = content_image.size

    print('Original content image size', original_content_image_size)
    print('Saving content image')
    content_image.save(params['content_image_path'])
    print('resizing')
    im_size = (params['image_width'], params['image_height'])
    content_image = content_image.resize(im_size, resample=Image.BICUBIC)
    print('Resized content imaged sixze', content_image.size)
    return content_image, original_content_image_size


def load_style_image(params):
    style_image = open_image(params['style_image_path'])
    print('Style image size', style_image.size)
    print('Saving style image')
    style_image.save(params['style_image_path'])
    print('resizing')
    im_size = (params['image_width'], params['image_height'])
    style_image = style_image.resize(im_size, resample=Image.BICUBIC)
    print('Resized style imaged size',style_image.size)
    return style_image


def get_initial_image(params, content_img, style_img, device):
    torch.manual_seed(params['random_seed'])
    if params['input_image'] == 'noise':
        input_img = torch.randn(content_img.data.size(), device=device)
    elif params['input_image'] == 'content':
        input_img = content_img.clone()
    elif params['input_image'] == 'style':
        input_img = style_img.clone()
    elif params['input_image'] == 'hybrid':
        input_img_noise = torch.randn(content_img.data.size(), device=device)
        input_img_content = content_img.clone()
        input_img_style = style_img.clone()
        w_content = params['hybrid_weight_content']
        w_style = params['hybrid_weight_style']
        w_noise = 1.0 - (w_content + w_style)
        assert 0 <= w_content <= 1
        assert 0 <= w_style <= 1
        assert w_noise >= 0.0
        input_img = w_noise * input_img_noise \
            + w_content * input_img_content \
            + w_style * input_img_style
    else:
        image = open_image(params['input_image']).resize(content_img.data.size())
        input_img = image_to_tensor(image)
        input_img += torch.randn(content_img.data.size(), device=device) * 0.05

    return input_img


def get_image_tensors(params, device):
    # get the content image
    content_image, original_content_image_size = load_content_image(params)

    # get the style image
    style_image = load_style_image(params)

    content_img = image_to_tensor(content_image, device)
    style_img = image_to_tensor(style_image, device)

    return content_img, style_img, original_content_image_size
