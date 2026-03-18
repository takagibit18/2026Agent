# #283.移动零
# class Solution:
#     def moveZeroes(self, nums: List[int]) -> None:
#         p1=0 #遍历用
#         p2=0 #存储数的位置
#         for p1 in range(0,len(nums)):
#             if nums[p1]!=0:
#                 nums[p1],nums[p2]=nums[p2],nums[p1]
#                 p2+=1
#             p1+=1

# #11.盛最多水的容器
# class Solution:
#     def maxArea(self, height: List[int]) -> int:
#         left=0
#         right=len(height)-1
#         max_square=0
#         current_square=0
#         while left<right:
#             if height[left]<height[right]:
#                 current_square=(right-left)*height[left]
#                 max_square=max(max_square,current_square)
#                 left+=1
#             else:
#                 current_square=(right-left)*height[right]
#                 max_square=max(max_square,current_square)
#                 right-=1
#         return max_square
    

#hot100 15.三数之和
#初次思考解法 O(n^2)的解法，哈希表存储两数之和，遍历第三个数，判断是否存在满足条件的两数之和
# 在面对大样本时运行超时
# class Solution:
#     def threeSum(self, nums: list[int]) -> list[list[int]]:
#         n = len(nums)
#         hashtable = {} # key: sum, value: list of [index_a, index_b]
#         trible_set = set() # 用于存储唯一的三元组元组

#         # 构建哈希表，存储每对数字的和及其索引
#         for a in range(n):
#             for b in range(a + 1, n):
#                 current_sum = nums[a] + nums[b]
#                 if current_sum not in hashtable:
#                     hashtable[current_sum] = []
#                 hashtable[current_sum].append([a, b]) # 存储索引

#         # 查找符合条件的三元组
#         for k in range(n): # 遍历第三个数字的索引
#             target_sum_for_pair = -nums[k]
#             if target_sum_for_pair in hashtable:
#                 for idx_pair in hashtable[target_sum_for_pair]:
#                     idx_a, idx_b = idx_pair[0], idx_pair[1]

#                     # 核心判断：确保三个索引彼此不同
#                     if idx_a != k and idx_b != k:
#                         # 找到有效的三元组，将其排序并转换为元组添加到 set
#                         triplet = sorted([nums[idx_a], nums[idx_b], nums[k]])
#                         trible_set.add(tuple(triplet))

#         return [list(t) for t in trible_set]
class Solution:
    def threeSum(self, nums: List[int]) -> List[List[int]]:
        n = len(nums)
        nums.sort()
        ans = list()
        
        # 枚举 a
        for first in range(n):
            # 需要和上一次枚举的数不相同
            if first > 0 and nums[first] == nums[first - 1]:
                continue
            # c 对应的指针初始指向数组的最右端
            third = n - 1
            target = -nums[first]
            # 枚举 b
            for second in range(first + 1, n):
                # 需要和上一次枚举的数不相同
                if second > first + 1 and nums[second] == nums[second - 1]:
                    continue
                # 需要保证 b 的指针在 c 的指针的左侧
                while second < third and nums[second] + nums[third] > target:
                    third -= 1
                # 如果指针重合，随着 b 后续的增加
                # 就不会有满足 a+b+c=0 并且 b<c 的 c 了，可以退出循环
                if second == third:
                    break
                if nums[second] + nums[third] == target:
                    ans.append([nums[first], nums[second], nums[third]])
        
        return ans
