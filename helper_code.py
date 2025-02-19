#!/usr/bin/env python

# Do *not* edit this script.
# These are helper functions that you can use with your code.
# Check the example code to see how to import these functions to your code.

import numpy as np
import os
import sys

### Challenge data I/O functions

# Find the records in a folder and its subfolders.
def find_records(folder):
    records = set()
    for root, directories, files in os.walk(folder):
        for file in files:
            extension = os.path.splitext(file)[1]
            if extension == '.hea':
                record = os.path.relpath(os.path.join(root, file), folder)[:-4]
                records.add(record)
    records = sorted(records)
    return records

# Load the header for a record.
def load_header(record):
    header_file = get_header_file(record)
    header = load_text(header_file)
    return header

# Load the signal(s) for a record.
def load_signal(record):
    import wfdb

    signal_files = get_signal_files(record)
    if signal_files:
        signal, fields = wfdb.rdsamp(record)
    else:
        signal, fields = None, None
    return signal, fields

def load_signals(record):
    return load_signal(record)

# Load the image(s) for a record.
def load_image(record):
    from PIL import Image

    path = os.path.split(record)[0]
    image_files = get_image_files(record)

    images = list()
    for image_file in image_files:
        image_file_path = os.path.join(path, image_file)
        if os.path.isfile(image_file_path):
            image = Image.open(image_file_path)
            images.append(image)

    return images

def load_images(record):
    return load_image(record)

# Load the dx class(es) for a record.
def load_dx(record):
    header = load_header(record)
    dx = get_dxs_from_header(header)
    return dx

def load_dxs(record):
    return load_dx(record)

# Save the header for a record.
def save_header(record, header):
    header_file = get_header_file(record)
    save_text(header_file, header)

# Save the signal(s) for a record.
def save_signal(record, signal, comments=list()):
    header = load_header(record)
    path, record = os.path.split(record)
    sampling_frequency = get_sampling_frequency(header)
    signal_formats = get_signal_formats(header)
    adc_gains = get_adc_gains(header)
    baselines = get_baselines(header)
    signal_units = get_signal_units(header)
    signal_names = get_signal_names(header)

    if all(signal_format == '16' for signal_format in signal_formats):
        signal = np.clip(signal, -2**15 + 1, 2**15 - 1)
        signal = np.asarray(signal, dtype=np.int16)
    else:
        signal_format_string = ', '.join(sorted(set(signal_formats)))
        raise NotImplementedError(f'{signal_format_string} not implemented')

    import wfdb
    wfdb.wrsamp(record, fs=sampling_frequency, units=signal_units, sig_name=signal_names, \
                d_signal=signal, fmt=signal_formats, adc_gain=adc_gains, baseline=baselines, comments=comments, \
                write_dir=path)

def save_signals(record, signals):
    save_signal(record, signals)

# Save the dx class(es) for a record.
def save_dx(record, dx):
    header_file = get_header_file(record)
    header = load_text(header_file)
    header += '#Dx: ' + ', '.join(dx) + '\n'
    save_text(header_file, header)
    return header

def save_dxs(record, dxs):
    return save_dx(record, dxs)

### Helper Challenge functions

# Load a text file as a string.
def load_text(filename):
    with open(filename, 'r') as f:
        string = f.read()
    return string

# Save a string as a text file.
def save_text(filename, string):
    with open(filename, 'w') as f:
        f.write(string)

# Get the record name from a header file.
def get_record_name(string):
    value = string.split('\n')[0].split(' ')[0].split('/')[0].strip()
    return value

# Get the number of signals from a header file.
def get_num_signals(string):
    value = string.split('\n')[0].split(' ')[1].strip()
    if is_integer(value):
        value = int(value)
    else:
        value = None
    return value

# Get the sampling frequency from a header file.
def get_sampling_frequency(string):
    value = string.split('\n')[0].split(' ')[2].split('/')[0].strip()
    if is_number(value):
        value = float(value)
    else:
        value = None
    return value

# Get the number of samples from a header file.
def get_num_samples(string):
    value = string.split('\n')[0].split(' ')[3].strip()
    if is_integer(value):
        value = int(value)
    else:
        value = None
    return value

# Get signal units from a header file.
def get_signal_formats(string):
    num_signals = get_num_signals(string)
    values = list()
    for i, l in enumerate(string.split('\n')):
        if 1 <= i <= num_signals:
            field = l.split(' ')[1]
            if 'x' in field:
                field = field.split('x')[0]
            if ':' in field:
                field = field.split(':')[0]
            if '+' in field:
                field = field.split('+')[0]
            value = field
            values.append(value)
    return values

# Get signal units from a header file.
def get_adc_gains(string):
    num_signals = get_num_signals(string)
    values = list()
    for i, l in enumerate(string.split('\n')):
        if 1 <= i <= num_signals:
            field = l.split(' ')[2]
            if '/' in field:
                field = field.split('/')[0]
            if '(' in field and ')' in field:
                field = field.split('(')[0]
            value = float(field)
            values.append(value)
    return values

# Get signal units from a header file.
def get_baselines(string):
    num_signals = get_num_signals(string)
    values = list()
    for i, l in enumerate(string.split('\n')):
        if 1 <= i <= num_signals:
            field = l.split(' ')[2]
            if '/' in field:
                field = field.split('/')[0]
            if '(' in field and ')' in field:
                field = field.split('(')[1].split(')')[0]
            value = int(field)
            values.append(value)
    return values

# Get signal units from a header file.
def get_signal_units(string):
    num_signals = get_num_signals(string)
    values = list()
    for i, l in enumerate(string.split('\n')):
        if 1 <= i <= num_signals:
            field = l.split(' ')[2]
            if '/' in field:
                value = field.split('/')[1]
            else:
                value = 'mV'
            values.append(value)
    return values

# Get the number of samples from a header file.
def get_signal_names(string):
    num_signals = get_num_signals(string)
    values = list()
    for i, l in enumerate(string.split('\n')):
        if 1 <= i <= num_signals:
            value = l.split(' ')[8]
            values.append(value)
    return values

# Get a variable from a string.
def get_variable(string, variable_name):
    variable = ''
    has_variable = False
    for l in string.split('\n'):
        if l.startswith(variable_name):
            variable = l[len(variable_name):].strip()
            has_variable = True
    return variable, has_variable

# Get variables from a text file.
def get_variables(string, variable_name, sep=','):
    variables = list()
    has_variable = False
    for l in string.split('\n'):
        if l.startswith(variable_name):
            variables += [variable.strip() for variable in l[len(variable_name):].strip().split(sep)]
            has_variable = True
    return variables, has_variable

# Get the signal file(s) from a header or a similar string.
def get_signal_files_from_header(string):
    signal_files = list()
    for i, l in enumerate(string.split('\n')):
        arrs = [arr.strip() for arr in l.split(' ')]
        if i==0 and not l.startswith('#'):
            num_channels = int(arrs[1])
        elif i<=num_channels and not l.startswith('#'):
            signal_file = arrs[0]
            if signal_file not in signal_files:
                signal_files.append(signal_file)
        else:
            break
    return signal_files

# Get the image file(s) from a header or a similar string.
def get_image_files_from_header(string):
    images, has_image = get_variables(string, '#Image:')
    if not has_image:
        raise Exception('No images available: did you forget to generate or include the images?')
    return images

# Get the dx class(es) from a header or a similar string.
def get_dxs_from_header(string):
    dxs, has_dx = get_variables(string, '#Dx:')
    if not has_dx:
        raise Exception('No dx classes available: are you trying to load the classes from the held-out dataset, or did you forget to prepare the data to include the classes?')
    return dxs

# Get the header file for a record.
def get_header_file(record):
    if not record.endswith('.hea'):
        header_file = record + '.hea'
    else:
        header_file = record
    return header_file

# Get the signal file(s) for a record.
def get_signal_files(record):
    header_file = get_header_file(record)
    header = load_text(header_file)
    signal_files = get_signal_files_from_header(header)
    return signal_files

# Get the image file(s) for a record.
def get_image_files(record):
    header_file = get_header_file(record)
    header = load_text(header_file)
    image_files = get_image_files_from_header(header)
    return image_files

### Evaluation functions

# Construct the binary one-vs-rest confusion matrices, where the columns are the expert labels and the rows are the classifier
# for the given classes.
def compute_one_vs_rest_confusion_matrix(labels, outputs, classes):
    assert np.shape(labels) == np.shape(outputs)

    num_instances = len(labels)
    num_classes = len(classes)

    A = np.zeros((num_classes, 2, 2))
    for i in range(num_instances):
        for j in range(num_classes):
            if labels[i, j] == 1 and outputs[i, j] == 1: # TP
                A[j, 0, 0] += 1
            elif labels[i, j] == 0 and outputs[i, j] == 1: # FP
                A[j, 0, 1] += 1
            elif labels[i, j] == 1 and outputs[i, j] == 0: # FN
                A[j, 1, 0] += 1
            elif labels[i, j] == 0 and outputs[i, j] == 0: # TN
                A[j, 1, 1] += 1

    return A

# Compute macro F-measure.
def compute_f_measure(labels, outputs):
    # Compute confusion matrix.
    classes = sorted(set.union(*map(set, labels)))
    labels = compute_one_hot_encoding(labels, classes)
    outputs = compute_one_hot_encoding(outputs, classes)
    A = compute_one_vs_rest_confusion_matrix(labels, outputs, classes)

    num_classes = len(classes)
    per_class_f_measure = np.zeros(num_classes)
    for k in range(num_classes):
        tp, fp, fn, tn = A[k, 0, 0], A[k, 0, 1], A[k, 1, 0], A[k, 1, 1]
        if 2 * tp + fp + fn > 0:
            per_class_f_measure[k] = float(2 * tp) / float(2 * tp + fp + fn)
        else:
            per_class_f_measure[k] = float('nan')

    if np.any(np.isfinite(per_class_f_measure)):
        macro_f_measure = np.nanmean(per_class_f_measure)
    else:
        macro_f_measure = float('nan')

    return macro_f_measure, per_class_f_measure, classes

# Reorder channels in signal.
def reorder_signal(input_signal, input_channels, output_channels):
    if input_signal is None:
        return None

    if input_channels == output_channels and len(set(input_channels)) == len(set(output_channels)) == len(output_channels):
        output_signal = input_signal
    else:
        input_channels = [channel.strip().casefold() for channel in input_channels]
        output_channels = [channel.strip().casefold() for channel in output_channels]

        num_samples = np.shape(input_signal)[0]
        num_channels = len(output_channels)
        data_type = input_signal.dtype
        output_signal = np.zeros((num_samples, num_channels), dtype=data_type)

        for i, output_channel in enumerate(output_channels):
            for j, input_channel in enumerate(input_channels):
                if input_channel == output_channel:
                    output_signal[:, i] += input_signal[:, j]

    return output_signal

# Pad or truncate signal.
def trim_signal(input_signal, num_samples):
    if input_signal is None:
        return None

    cur_samples, num_channels = np.shape(input_signal)
    data_type = input_signal.dtype

    if cur_samples == num_samples:
        output_signal = input_signal
    else:
        output_signal = np.zeros((num_samples, num_channels), dtype=data_type)
        if cur_samples < num_samples: # Zero-pad the signals.
            output_signal[:cur_samples, :] = input_signal
        else: # Truncate the signals.
            output_signal = input_signal[:num_samples, :]

    return output_signal

# Compute SNR.
def compute_snr(label_signal, output_signal):
    label_signal = np.asarray(label_signal)
    output_signal = np.asarray(output_signal)
    assert(np.all(np.shape(label_signal) == np.shape(output_signal)))

    label_signal[np.isnan(label_signal)] = 0
    output_signal[np.isnan(output_signal)] = 0

    noise_signal = output_signal - label_signal

    x = np.sum(label_signal**2)
    y = np.sum(noise_signal**2)

    if x > 0 and y > 0:
        snr = 10 * np.log10(x / y)
    elif x > 0 and y == 0:
        snr = float('inf')
    else:
        snr = float('nan')

    return snr

# Compute the mean signal power to median noise power metric.
def compute_snr_median(label_signal, output_signal):
    label_signal = np.asarray(label_signal)
    output_signal = np.asarray(output_signal)
    assert(np.all(np.shape(label_signal) == np.shape(output_signal)))

    label_signal[np.isnan(label_signal)] = 0
    output_signal[np.isnan(output_signal)] = 0

    noise_signal = output_signal - label_signal

    x = np.mean(label_signal**2)
    y = np.median(noise_signal**2)

    if y > 0:
        snr = 10 * np.log10(x / y)
    else:
        snr = float('inf')

    return snr

# Compute a metric inspired by the Kolmogorov-Smirnov test statistic.
def compute_ks_metric(label_signal, output_signal):
    label_signal = np.asarray(label_signal)
    output_signal = np.asarray(output_signal)
    assert(np.all(np.shape(label_signal) == np.shape(output_signal)))

    label_signal[np.isnan(label_signal)] = 0
    output_signal[np.isnan(output_signal)] = 0

    label_signal_cdf = np.cumsum(np.abs(label_signal))
    output_signal_cdf = np.cumsum(np.abs(output_signal))

    if label_signal_cdf[-1] > 0:
        label_signal_cdf = label_signal_cdf / label_signal_cdf[-1]
    if output_signal_cdf[-1] > 0:
        output_signal_cdf = output_signal_cdf / output_signal_cdf[-1]

    goodness_of_fit = 1.0 - np.max(np.abs(label_signal_cdf - output_signal_cdf))

    return goodness_of_fit

# Compute the adaptive signed correlation index (ASCI) metric.
def compute_asci_metric(label_signal, output_signal, beta=0.05):
    label_signal = np.asarray(label_signal)
    output_signal = np.asarray(output_signal)
    assert(np.all(np.shape(label_signal) == np.shape(output_signal)))

    label_signal[np.isnan(label_signal)] = 0
    output_signal[np.isnan(output_signal)] = 0

    if beta <= 0 or beta > 1:
        raise ValueError('The beta value should be greater than 0 and less than or equal to 1.')

    threshold = beta * np.std(label_signal)

    noise_signal = np.abs(label_signal - output_signal)

    discrete_noise = np.zeros_like(noise_signal)
    discrete_noise[noise_signal <= threshold] = 1
    discrete_noise[noise_signal > threshold] = -1

    asci = np.mean(discrete_noise)

    return asci

# Compute a weighted absolute difference metric.
def compute_weighted_absolute_difference(label_signal, output_signal, fs):
    label_signal = np.asarray(label_signal)
    output_signal = np.asarray(output_signal)
    assert(label_signal.ndim == 1 and np.size(label_signal) == np.size(output_signal))

    from scipy.signal import filtfilt

    label_signal[np.isnan(label_signal)] = 0
    output_signal[np.isnan(output_signal)] = 0

    m = np.size(label_signal)
    w = filtfilt(np.ones(m), m, label_signal, method='gust')
    w = 1 - 0.5/np.max(w) * w
    n = np.sum(w)
    
    weighted_absolute_difference_metric = np.sum(np.abs(label_signal-output_signal) * w)/n

    return weighted_absolute_difference_metric

### Other helper functions

# Check if a variable is a number or represents a number.
def is_number(x):
    try:
        float(x)
        return True
    except (ValueError, TypeError):
        return False

# Check if a variable is an integer or represents an integer.
def is_integer(x):
    if is_number(x):
        return float(x).is_integer()
    else:
        return False

# Check if a variable is a finite number or represents a finite number.
def is_finite_number(x):
    if is_number(x):
        return np.isfinite(float(x))
    else:
        return False

# Check if a variable is a NaN (not a number) or represents a NaN.
def is_nan(x):
    if is_number(x):
        return np.isnan(float(x))
    else:
        return False

# Cast a value to an integer if an integer, a float if a non-integer float, and an unknown value otherwise.
def cast_int_float_unknown(x):
    if is_integer(x):
        x = int(x)
    elif is_finite_number(x):
        x = float(x)
    elif is_number(x):
        x = 'Unknown'
    else:
        raise NotImplementedError(f'Unable to cast {x}.')
    return x

# Construct the one-hot encoding of data for the given classes.
def compute_one_hot_encoding(data, classes):
    num_instances = len(data)
    num_classes = len(classes)

    one_hot_encoding = np.zeros((num_instances, num_classes), dtype=np.bool_)
    unencoded_data = list()
    for i, x in enumerate(data):
        for y in x:
            for j, z in enumerate(classes):
                if (y == z) or (is_nan(y) and is_nan(z)):
                    one_hot_encoding[i, j] = 1

    return one_hot_encoding