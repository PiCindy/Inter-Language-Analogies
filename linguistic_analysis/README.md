# nlg module

Python3 package for analogy purpose.

Version: 3.2.1
License: This module is under GPLv3 license.


## Dependencies:
1. swig (wrapper for C program)
2. Python libraries:
	- numpy
	- matplotlib
	- tabulate
3. Depends on your environment, you may also need to install Cython (for matplotlib)


## How to install:
1. Install fast_distance module
	- Download:  
		- EBMT/NLP Lab homepage: http://lepage-lab.ips.waseda.ac.jp/media/filer_public/b7/d8/b7d87323-51e6-42c7-bbed-29594b7df8cf/fast_distance_in_c.zip
	- Extract the zip file
	- Follow the instruction in README file to install
2. nlg
	- Extract the zip file
	- Open Terminal
	- Go inside the extracted directory where setup.py script is located
	- Install (__-e__ is optional for edit mode)
		>$ pip install [-e] .


## Check the installation

- Use the following command to test the help:  
	>$ python3 Words2Clusters.py -h

- Use the following commands to test the execution:
	>$ printf "toto\ntata\npopo\npapa\n" | python3 Words2Clusters.py -V

- You should get the following output on your terminal.

	> \# Reading words and computing feature vectors (features=characters)...  
	> \# Clustering the words according to their feature vectors...  
	> \# Add the indistinguishables...  
	> \# Checking distance constraints...  
	> \#   
	> toto : tata :: popo : papa  
	> toto : popo :: tata : papa  

---
### Contact
If you encounter any problem, please do not hesitate to contact us.
	fam.rashel@fuji.waseda.jp
	yves.lepage@waseda.jp