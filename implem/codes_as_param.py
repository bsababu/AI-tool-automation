# import ast
# import pydot
# from IPython.display import display, Image
# import uuid
# import os
# from graphviz import Digraph
# dot = Digraph()


# code = """
# def euclidean_gcd(a, b):
#     while b != 0:
#         a, b = b, a % b
#     return a
#     """


def merge_sort(arr):
    if len(arr) > 1:
        mid = len(arr) // 2
        left = arr[:mid]
        right = arr[mid:]

        merge_sort(left)
        merge_sort(right)

        i = j = k = 0

        while i < len(left) and j < len(right):
            if left[i] < right[j]:
                arr[k] = left[i]
                i += 1
            else:
                arr[k] = right[j]
                j += 1
            k += 1

        while i < len(left):
            arr[k] = left[i]
            i += 1
            k += 1

        while j < len(right):
            arr[k] = right[j]
            j += 1
            k += 1
    return arr

# def add_node(node, parent=None):
#     node_name = str(node.__class__.__name__)
#     dot.node(str(id(node)), node_name)
#     if parent:
#         dot.edge(str(id(parent)), str(id(node)))
#     for child in ast.iter_child_nodes(node):
#         add_node(child, node)

# tree = ast.parse(code)
# add_node(tree)

# COLOR_MAP = {
#     'Module': '#FFDDA2',
#     'FunctionDef': '#F4A261',
#     'arguments': '#E0BBE4',
#     'arg': '#95E1D3',
#     'Assign': '#98FB98',
#     'Name': '#87CEEB',
#     'If': '#FFB6B9',
#     'Compare': '#FFA987',
#     'While': '#C0A0F0',
#     'For': '#C0A0F0',
#     'Call': '#FFFF99',
#     'Return': '#FF6961',
#     'BinOp': '#FAEBD7',
#     'Subscript': '#D8BFD8',
#     'Expr': '#DCDCDC',
# }

# def add_nodes_edges(node, parent_node_name=None, graph=None):
#     global node_counter
#     # Assign unique ID to each node
#     node_name = f"{str(uuid.uuid4())}"
    
#     # Get label and color based on node type
#     label = type(node).__name__
#     color = COLOR_MAP.get(label, "#FFFFFF")
    
#     # Add node to graph
#     graph.add_node(pydot.Node(node_name, label=label, style='filled', fillcolor=color))

#     # Add edge from parent
#     if parent_node_name:
#         graph.add_edge(pydot.Edge(parent_node_name, node_name))

#     # Recursively process children
#     for child in ast.iter_child_nodes(node):
#         add_nodes_edges(child, node_name, graph)

# # Create a new PyDot graph
# graph = pydot.Dot("AST", graph_type="digraph", bgcolor="#FFFFFF")

# # Start adding nodes from root
# add_nodes_edges(tree, None, graph)

# # Save graph to file and display
# filename = "ast_merge_sort.png"
# # graph.write_png(filename)

# # Display the image in Jupyter Notebook or save separately
# # display(Image(filename=filename))
# print