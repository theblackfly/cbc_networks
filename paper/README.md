# Experiments scripts
This folder contains all scripts required to replicate the results presented 
in the main part of the paper and some additional scripts to replicate the 
results on the GTSRB and Cifar10 dataset found in the supplementary. 

While most parameters for the scripts are hard coded in line with the settings 
used in the paper, some settings are available as command line parameters. 
These parameters are dependent on the architecture on which the script is ran 
and therefore impossible to specify before hand. However, when these 
parameters are not specified when the script is called, the default values 
will represent the setting used in the paper.

You can call an experiment by

```python <script_name>.py```

followed by a list of parameters in the form:

```--<parameter_name> <[optional]parameter_value>```

## Parameters
The following standard parameter settings are available.

|parameter|type|purpose|note|
|---|---|---|---|
|weights|str|Load *.h5 model trained weights||
|save_dir|str|Output directory|Defaults to './output'|
|epochs|int|Number of epochs the model is trained for|Handle with care for the CBCs for CIFAR-10 and GTSRB as they require custom loss schedulers.|
|lr|float|Initial learning rate of the optimizer||
|batch_size|int|Batch size used to train the model||
|gpu|int|Index of the GPU used during training|For the experiments on ImageNet, two gpus need to be specified seperated by a comma.|
|eval|flag|Skips training and instead only evaluates the model||
