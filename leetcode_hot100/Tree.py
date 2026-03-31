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

 # 226. Invert Binary Tree
    # Definition for a binary tree node.
# class TreeNode:
#     def __init__(self, val=0, left=None, right=None):
#         self.val = val
#         self.left = left
#         self.right = right
class Solution:
    def invertTree(self, root: Optional[TreeNode]) -> Optional[TreeNode]:
        if not root: return#**最重要,不设置终止条件会无限递归
        left=self.invertTree(root.left)
        right=self.invertTree(root.right)
        root.left,root.right=right,left
        return root

# 101. Symmetric Tree
class Solution:
    def isSymmetric(self, root: Optional[TreeNode]) -> bool:
        if not root:return
        def recur(L, R):
            if not L and not R: return True
            if not L or not R or L.val != R.val: return False
            return recur(L.left, R.right) and recur(L.right, R.left)

        return not root or recur(root.left, root.right)