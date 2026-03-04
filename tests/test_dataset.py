import src.jbfoundry as jbf

print("AdvBench")
dataset = jbf.read_dataset("advbench")
row = dataset[0]  # Get first row
print(row)

print("HarmBench")
dataset = jbf.read_dataset("harmbench")
row = dataset[0]  # Get first row
print(row)

print("HarmBench Contextual")
dataset = jbf.read_dataset("harmbench-contextual")
row = dataset[0]  # Get first row
print(row)

print("HarmBench Copyright")
dataset = jbf.read_dataset("harmbench-copyright")
row = dataset[0]  # Get first row
print(row)

print("HarmBench Standard")
dataset = jbf.read_dataset("harmbench-standard")
row = dataset[0]  # Get first row
print(row)

print("JBB Harmful")
dataset = jbf.read_dataset("jbb-harmful")
row = dataset[0]  # Get first row
print(row)

print("JBB Benign")
dataset = jbf.read_dataset("jbb-benign")
row = dataset[0]  # Get first row
print(row)

print("JBB All")
dataset = jbf.read_dataset("jbb-all")
row = dataset[0]  # Get first row
print(row)