#283.移动零
class Solution:
    def moveZeroes(self, nums: List[int]) -> None:
        p1=0 #遍历用
        p2=0 #存储数的位置
        for p1 in range(0,len(nums)):
            if nums[p1]!=0:
                nums[p1],nums[p2]=nums[p2],nums[p1]
                p2+=1
            p1+=1

#11.盛最多水的容器
class Solution:
    def maxArea(self, height: List[int]) -> int:
        left=0
        right=len(height)-1
        max_square=0
        current_square=0
        while left<right:
            if height[left]<height[right]:
                current_square=(right-left)*height[left]
                max_square=max(max_square,current_square)
                left+=1
            else:
                current_square=(right-left)*height[right]
                max_square=max(max_square,current_square)
                right-=1
        return max_square