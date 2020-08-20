import torch as t
from bnn_priors.data import UCI, CIFAR10, CIFAR10_C, MNIST, RotatedMNIST
from bnn_priors.models import RaoBDenseNet, DenseNet, PreActResNet18, PreActResNet34, ClassificationDenseNet
from bnn_priors.prior import LogNormal
from bnn_priors import prior


def device(device):
    if device == "try_cuda":
        if t.cuda.is_available():
            return t.device("cuda:0")
        else:
            return t.device("cpu")
    return t.device(device)


def get_data(data, device):
    assert data[:3] == "UCI" or data[:8] == "cifar10c" or data in ["cifar10",
                        "mnist", "rotated_mnist"], f"Unknown data set {data}"
    if data[:3] == "UCI":
        uci_dataset = data.split("_")[1]
        assert uci_dataset in ["boston", "concrete", "energy", "kin8nm",
                               "naval", "power", "protein", "wine", "yacht"]
        # TODO: do we ever use a different split than 0?
        dataset = UCI(uci_dataset, 0, device=device)
    elif data[:8] == "cifar10c":
        corruption = data.split("-")[1]
        dataset = CIFAR10_C(corruption, device=device)
    elif data == "cifar10":
        dataset = CIFAR10(device=device)
    elif data == "mnist":
        dataset = MNIST(device=device)
    elif data == "rotated_mnist":
        dataset = RotatedMNIST(device=device)
    return dataset


def get_prior(prior_name):
    priors = {"gaussian": prior.Normal,
             "lognormal": prior.LogNormal,
             "laplace": prior.Laplace,
             "cauchy": prior.Cauchy,
             "student-t": prior.StudentT,
             "uniform": prior.Uniform}
    assert prior_name in priors
    return priors[prior_name]


def get_model(x_train, y_train, model, width, weight_prior, weight_loc,
             weight_scale, bias_prior, bias_loc, bias_scale, batchnorm):
    assert model in ["densenet", "raobdensenet", "resnet18", "resnet34", "classificationdensenet"]
    if weight_prior in ["cauchy"]:
        #TODO: which other distributions should use this? Laplace?
        scaling_fn = lambda std, dim: std/dim
    else:
        scaling_fn = lambda std, dim: std/dim**0.5
    weight_prior = get_prior(weight_prior)
    bias_prior = get_prior(bias_prior)
    if model == "densenet":
        net = DenseNet(x_train.size(-1), y_train.size(-1), width, noise_std=LogNormal((), -1., 0.2),
                        prior_w=weight_prior, loc_w=weight_loc, std_w=weight_scale,
                        prior_b=bias_prior, loc_b=bias_loc, std_b=bias_scale, scaling_fn=scaling_fn).to(x_train)
    elif model == "raobdensenet":
        net = RaoBDenseNet(x_train, y_train, width, noise_std=LogNormal((), -1., 0.2)).to(x_train)
    elif model == "classificationdensenet":
        net = ClassificationDenseNet(x_train.size(-1), y_train.max()+1, width, softmax_temp=1.,
                        prior_w=weight_prior, loc_w=weight_loc, std_w=weight_scale,
                        prior_b=bias_prior, loc_b=bias_loc, std_b=bias_scale, scaling_fn=scaling_fn).to(x_train)
    elif model == "resnet18":
        net = PreActResNet18(prior_w=weight_prior, loc_w=weight_loc, std_w=weight_scale,
                            prior_b=bias_prior, loc_b=bias_loc, std_b=bias_scale, scaling_fn=scaling_fn,
                            bn=batchnorm, softmax_temp=1.).to(x_train)
    elif model == "resnet34":
        net = PreActResNet34(prior_w=weight_prior, loc_w=weight_loc, std_w=weight_scale,
                            prior_b=bias_prior, loc_b=bias_loc, std_b=bias_scale, scaling_fn=scaling_fn,
                            bn=batchnorm, softmax_temp=1.).to(x_train)
    return net