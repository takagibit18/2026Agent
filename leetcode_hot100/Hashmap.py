# hashmap={"apple":5,"banana":3,"orange":2}
# # print(hashmap["apple"]) 欠佳
# print(hashmap.get("grape"))

# if "banana" in hashmap:
#     print(hashmap["banana"])

 #HOT100 1.两数之和
class Solution:
    def twoSum(self, nums: List[int], target: int) -> List[int]:
        hashtable = dict()
        for i, num in enumerate(nums):
            if target - num in hashtable:
                return [hashtable[target - num], i]
            hashtable[nums[i]] = i
        return []


#HOT100 49.字母异位词分组
class Solution:
    def groupAnagrams(self, strs: List[str]) -> List[List[str]]:
        mp = collections.defaultdict(list)

        for st in strs:
            counts = [0] * 26 # 写在循环外面，避免重复创建列表
            for ch in st:
                counts[ord(ch) - ord("a")] += 1
            # 需要将 list 转换成 tuple 才能进行哈希
            mp[tuple(counts)].append(st)# defaultdict 的 value 是一个 list
        
        return list(mp.values())

#HOT100 128.最长连续序列
class Solution:
    def longestConsecutive(self, nums: List[int]) -> int:
        hashtable=dict()
        current_len=max_len=0
        set_nums=set(nums) #去重(哈希表的key不能重复)
        for i in set_nums:
            if i-1 not in set_nums:
                current_num=i
                current_len=1

                while current_num+1 in set_nums:
                    current_num+=1
                    current_len+=1
                max_len=max(max_len,current_len)
        return max_len
                