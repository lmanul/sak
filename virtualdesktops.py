ARABIC = "1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16 17 18 19 20"
ROMAN  = "I II III IV V VI VII VIII IX X XI XII XIII XIV XV XVI XVII XVIII XIX XX"
CHINESE = "一 二 三 四 五 六 七 八 九 十 十一 十二 十三 十四 十五 十六 十七 十八 十九 二十"

SETS = [ ARABIC, ROMAN, CHINESE ]

ALL = [ARABIC, ROMAN, CHINESE]

# Takes a 1-based index
def name_from_index(index, n_rows, n_cols):
    zero_based_index = index - 1
    selected_set = (zero_based_index // (n_rows * n_cols)) % len(SETS)
    print("Selected " + str(selected_set))
    index_in_set = zero_based_index % (n_rows * n_cols)
    print("Index in set " + str(index_in_set))
    return ALL[selected_set][index_in_set]
