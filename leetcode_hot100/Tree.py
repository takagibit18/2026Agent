#94 Binary Tree Inorder Traversal
# class Solution:
#     def inorderTraversal(self, root: Optional[TreeNode]) -> List[int]:
#         output=[]
#         if root == None:
#             return output
#         else:
#             output.extend(self.inorderTraversal(root.left))
#             output.append(root.val)
#             output.extend(self.inorderTraversal(root.right))
#             return output


# 104 Maximum Depth of Binary Tree
class Solution:
    def maxDepth(self, root):
        if root is None: 
            return 0 
        else: 
            left_height = self.maxDepth(root.left) 
            right_height = self.maxDepth(root.right) 
            return max(left_height, right_height) + 1 
