#!/usr/bin/env python3

import sys

class Node:
    def __init__(self, label):
        self.label = label
        self.children = []

def parse_subtree(s, i=0):
    """
    Parse a subtree starting at s[i], where s[i] == '('.
    Returns (node, new_index).
    """
    # Expect '(' at the current position
    if s[i] != '(':
        raise ValueError("Expected '(' at position {}".format(i))
    i += 1  # move past '('

    # Gather the label until we hit either '(' or ')'
    label_start = i
    while i < len(s) and s[i] not in "()":
        i += 1
    label = s[label_start:i]

    # Create the node
    node = Node(label)

    # If we have subtrees, they will each start with '('
    # Keep parsing children until we reach ')'
    while i < len(s) and s[i] == '(':
        child, i = parse_subtree(s, i)
        node.children.append(child)

    # Expect a ')' now
    if i >= len(s) or s[i] != ')':
        raise ValueError("Expected ')' at position {}".format(i))
    i += 1  # move past ')'

    return node, i

def collect_paths(node, current_path=None, paths=None):
    """
    Perform a DFS from 'node' down to each leaf, building
    a list of label-paths (concatenated strings).
    """
    if current_path is None:
        current_path = []
    if paths is None:
        paths = []

    # Add current node's label to the path
    current_path.append(node.label)

    # If no children, it's a leaf: record the path
    if not node.children:
        # Concatenate all labels into a single string
        paths.append(''.join(current_path))
    else:
        # Otherwise recurse on each child
        for c in node.children:
            collect_paths(c, current_path, paths)

    # Backtrack
    current_path.pop()
    return paths

def main():
    if len(sys.argv) < 2:
        print("Usage: python parse_tree.py <input_file>")
        sys.exit(1)

    input_file = sys.argv[1]

    # Read the file and strip newlines
    with open(input_file, 'r') as f:
        content = f.read()
    content = content.replace('\n', '').replace('\r', '')

    # Parse the content as a tree
    root, _ = parse_subtree(content, 0)

    # Collect all paths from the root to the leaves
    paths = collect_paths(root)

    # Write them to output.tsv
    with open('output.tsv', 'w') as out:
        for p in paths:
            out.write(p + '\n')

if __name__ == "__main__":
    main()

