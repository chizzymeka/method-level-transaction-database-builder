### About the System

This program asks the user for a directory path containing one or more software systems cloned from GitHub. It then proceeds to develop a method-level transaction database for each system.

The transaction database features essential information such as the number of Java source files affected by a commit, the list of method Ids modified under the commit and the transaction frequency.

The transaction frequency is the number of times a group of modified methods has been changed together in the system.

This information could help determine if a commit is vulnerability-prone using anomaly detection-based software vulnerability prediction.