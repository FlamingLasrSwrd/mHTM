# parameter_exploration.py
#	
# Author         : James Mnatzaganian
# Contact        : http://techtorials.me
# Organization   : NanoComputing Research Lab - Rochester Institute of
# Technology
# Website        : https://www.rit.edu/kgcoe/nanolab/
# Date Created   : 02/07/16
# 
# Description    : Experiment for studying parameter affects.
# Python Version : 2.7.X
#
# License        : MIT License http://opensource.org/licenses/mit-license.php
# Copyright      : (c) 2016 James Mnatzaganian

"""
Experiment for studying parameter effects.

G{packagetree mHTM}
"""

__docformat__ = 'epytext'

# Native imports
import os, json, cPickle, sys

# Third party imports
import numpy as np

# Program imports
from mHTM.parallel import ConfigGenerator, create_runner, execute_runner
from mHTM.region import SPRegion
from mHTM.datasets.loader import SPDataset
from mHTM.metrics import SPMetrics

def generate_seeds(nseeds=10, seed=123456789):
	"""
	Create some random seeds.
	
	@param nseeds: The number of seeds to create.
	
	@param seed: The seed to use to initialize this function.
	
	@return: A list containing the seeds.
	"""
	
	# Set the random state
	np.random.seed(seed)
	return [int(x) for x in (np.random.random_sample(nseeds) * 1e9)]

def create_base_config(base_dir, experiment_name, global_inhibition=True,
	seed=None):
	"""
	Create the base configuration for the experiments.
	
	@param base_dir: The base directory, where all experiments will be stored.
	
	@param experiment_name: The name of the experiment being conducted.
	
	@param global_inhibition: If True global inhibition will be used;
	otherwise, local inhibition will be used.
	
	@param seed: The random seed to use. Use None to select a random one.
	
	@return: A dictionary containing the base configuration for the SP.
	"""
	
	return {
		'ninputs': 100,
		'ncolumns': 300,
		'pct_active': None,
		'nactive': 6,
		'global_inhibition': global_inhibition,
		'trim': 1e-4,
		'disable_boost': True,
		'seed': seed,
		'nsynapses': 20,
		'seg_th': 2,
		'syn_th': 0.5,
		'pinc': 0.01,
		'pdec': 0.01,
		'pwindow': 0.5,
		'random_permanence': True,
		'nepochs': 10,
		'log_dir': os.path.join(base_dir, 'global' if global_inhibition else
			'local', experiment_name)
	}

def run_experiment(experiments, base_dir, nsamples=500, nbits=100,
	pct_active=0.4, pct_noise=0.15, seed=123456789, ntrials=10,
	partition_name='debug', this_dir=os.getcwd()):
	"""
	Run an experiment for the SP. This experiment is used to vary various sets
	of parameters on the SP dataset. This function uses SLURM to conduct the
	experiments.
	
	@param experiments: A list containing the experiments details. Refer to one
	of the examples in this module for more details.
	
	@param base_dir: The base directory to use for logging.
	
	@param nsamples: The number of samples to add to the dataset.
	
	@param nbits: The number of bits each sample should have.
	
	@param pct_active: The percentage of bits that will be active in the base
	class SDR.
	
	@param pct_noise: The percentage of noise to add to the data.
	
	@param seed: The seed used to initialize the random number generator.
	
	@param ntrials: The number of parameter trials to use. Each iteration will
	be used to initialize the SP in a different manner.
	
	@param partition_name: The partition name of the cluster to use.
	
	@param this_dir: The full path to the directory where this file is located.
	"""
	
	# Create the dataset
	data = SPDataset(nsamples, nbits, pct_active, pct_noise, seed).data
	
	# Metrics
	metrics = SPMetrics()
	
	# Get the metrics for the dataset
	uniqueness_data = metrics.compute_uniqueness(data)
	overlap_data = metrics.compute_overlap(data)
	correlation_data = 1 - metrics.compute_distance(data)
	
	# Prep each experiment for execution
	for experiment_name, time_limit, memory_limit, params in experiments:
		# Iterate through each type of inhibition type
		for i, global_inhibition in enumerate((True, False)):
			# Get base configuration
			base_config = create_base_config(base_dir, experiment_name,
				global_inhibition)
			
			# Add the parameters
			for param_name, param_value in params:
				base_config[param_name] = param_value
				config_gen = ConfigGenerator(base_config, ntrials)
			
			# Make the configurations
			for config in config_gen.get_config():
				# Make the base directory
				dir = config['log_dir']
				splits = os.path.basename(dir).split('-')
				base_name = '-'.join(s for s in splits[:-1])
				dir = os.path.join(os.path.dirname(dir), base_name)
				try:
					os.makedirs(dir)
				except OSError:
					pass
				
				# Dump the config as JSON
				s = json.dumps(config, sort_keys=True, indent=4,
					separators=(',', ': ')).replace('},', '},\n')
				with open(os.path.join(dir, 'config.json'), 'wb') as f:
					f.write(s)
				
				# Dump the dataset and the metrics
				with open(os.path.join(dir, 'dataset.pkl'), 'wb') as f:
					cPickle.dump(data, f, cPickle.HIGHEST_PROTOCOL)
					cPickle.dump((uniqueness_data, overlap_data,
						correlation_data), f, cPickle.HIGHEST_PROTOCOL)
				
				# Create the runner
				this_path = os.path.join(this_dir, 'parameter_exploration.py')
				command = 'python "{0}" "{1}" {2} {3}'.format(this_path, dir,
					ntrials, seed)
				runner_path = os.path.join(dir, 'runner.sh')
				job_name = '{0}_{1}{2}'.format(experiment_name, 'G' if
					global_inhibition else 'L', base_name)
				stdio_path = os.path.join(dir, 'stdio.txt')
				stderr_path = os.path.join(dir, 'stderr.txt')
				create_runner(command=command, runner_path=runner_path,
					job_name=job_name, partition_name=partition_name,
					stdio_path=stdio_path, stderr_path=stderr_path,
					time_limit=time_limit[i], memory_limit=memory_limit)
				
				# Execute the runner
				execute_runner(runner_path)

def first_order_effects(base_dir, nsamples=500, nbits=100, pct_active=0.4,
	pct_noise=0.15, seed=123456789, ntrials=10, partition_name='debug',
	this_dir=os.getcwd()):
	"""
	Explore the effects of first order parameter effects on the quality of the
	SP's SDRs. This function uses SLURM to conduct the experiments.
	
	@param base_dir: The base directory to use for logging.
	
	@param nsamples: The number of samples to add to the dataset.
	
	@param nbits: The number of bits each sample should have.
	
	@param pct_active: The percentage of bits that will be active in the base
	class SDR.
	
	@param pct_noise: The percentage of noise to add to the data.
	
	@param seed: The seed used to initialize the random number generator.
	
	@param ntrials: The number of parameter trials to use. Each iteration will
	be used to initialize the SP in a different manner.
	
	@param partition_name: The partition name of the cluster to use.
	
	@param this_dir: The full path to the directory where this file is located.
	"""
	
	# Configure the experiments being run - see inline comments for details
	experiments = [
		# First experiment
		[
			# Experiment name
			'ncolumns',
			
			# Max time needed to perform one parameter set for this experiment
			# times the number of trials. The first time is for global
			# inhibition and the second time is for local inhibition.
			['00-00:30:00', '00-01:00:00'],
			
			# Max memory needed for each trial
			512,
			
			# Parameter sets
			[
				# First parameter
				[
					# Parameter name
					'ncolumns',
					
					# Parameter's values
					np.arange(5, 20, 5)
				]
			]
		],
		
		# Second experiment
		[
			'nactive',
			['00-00:30:00', '00-01:00:00'],
			512,
			[
				# First parameter
				['nactive', np.arange(1, 4)],
				
				# Second parameter
				['pct_active', None]
			]
		]
	]
	
	# Do the experiments!
	run_experiment(experiments, base_dir, nsamples, nbits, pct_active,
		pct_noise, seed, ntrials=ntrials, partition_name=partition_name,
		this_dir=this_dir)

def run_single_experiment(base_dir, ntrials=10, seed=123456789):
	"""
	Run the actual experiment.
	
	@param base_dir: The directory to containing the experiment to be run.
	
	@param ntrials: The number of trials to perform with different seeds.
	
	@param seed: The initial seed used to generate the other random seeds.
	"""
	
	# Generate the number of requested seeds
	seeds = generate_seeds(ntrials, seed)
	
	# Get the configuration
	with open(os.path.join(base_dir, 'config.json'), 'rb') as f:
		config = json.load(f)
	
	# Get the data and base metric data
	with open(os.path.join(base_dir, 'dataset.pkl'), 'rb') as f:
		data = cPickle.load(f)
		uniqueness_data, overlap_data, correlation_data = cPickle.load(f)
	
	# Metrics
	metrics = SPMetrics()
	
	# Execute each run
	for s in seeds:
		# Update the seed
		config['seed'] = s
		
		# Create the SP
		sp = SPRegion(**config)
		
		# Fit the SP
		sp.fit(data)
		
		# Get the SP's output
		sp_output = sp.predict(data)
		
		# Log all of the metrics
		sp._log_stats('Input Uniqueness', uniqueness_data)
		sp._log_stats('Input Overlap', overlap_data)
		sp._log_stats('Input Correlation', correlation_data)
		sp._log_stats('SP Uniqueness', metrics.compute_uniqueness(sp_output))
		sp._log_stats('SP Overlap', metrics.compute_overlap(sp_output))
		sp._log_stats('SP Correlation', 1 - metrics.compute_distance(
			sp_output))

if __name__ == '__main__':
	# Determine the mode of operation
	if len(sys.argv) == 1:
		# Configure the basic settings
		user_path = os.path.expanduser('~')
		this_dir = os.path.join(user_path, 'mHTM', 'dev')
		base_path = os.path.join(user_path, 'results')		
		ntrials = 3
		partition_name = 'debug'
		
		# Start the first order experiments
		first_order_effects(os.path.join(base_path, 'first_order'),
			ntrials=ntrials, this_dir=this_dir, partition_name=partition_name)
	elif len(sys.argv) == 4:
		# Get the provided input
		base_dir = sys.argv[1]
		ntrials = int(sys.argv[2])
		seed = int(sys.argv[3])
		
		# Launch this experiment
		run_single_experiment(base_dir, ntrials, seed)
