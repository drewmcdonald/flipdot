import pytest
import numpy as np
from flipdot.DotMatrix import DotMatrix, NPDotArray

# Helper function to create a DotMatrix from a list of lists
def mat(data: list[list[int]]) -> NPDotArray:
    return np.array(data, dtype=np.uint8)

class TestDotMatrix:
    def test_init_and_properties(self):
        m_data = mat([[1, 0], [0, 1]])
        dm = DotMatrix(m_data)
        assert np.array_equal(dm.mat, m_data)
        assert dm.shape == (2, 2)
        assert dm.height == 2
        assert dm.width == 2

    def test_from_shape(self):
        dm = DotMatrix.from_shape((3, 4))
        assert dm.shape == (3, 4)
        assert np.array_equal(dm.mat, np.zeros((3, 4), dtype=np.uint8))

    def test_clear(self):
        dm = DotMatrix(mat([[1, 1], [1, 1]]))
        dm.clear()
        assert np.array_equal(dm.mat, np.zeros((2, 2), dtype=np.uint8))

    def test_pad(self):
        dm = DotMatrix(mat([[1]]))
        padded_dm = dm.pad(((1, 1), (1, 1))) # Pad 1 all sides
        expected = mat([
            [0, 0, 0],
            [0, 1, 0],
            [0, 0, 0]
        ])
        assert np.array_equal(padded_dm.mat, expected)
        assert padded_dm.shape == (3, 3)

    def test_vpad(self):
        dm = DotMatrix(mat([[1]]))
        padded_dm = dm.vpad((1, 1)) # Pad 1 top, 1 bottom
        expected = mat([
            [0],
            [1],
            [0]
        ])
        assert np.array_equal(padded_dm.mat, expected)
        assert padded_dm.shape == (3, 1)

    def test_hpad(self):
        dm = DotMatrix(mat([[1]]))
        padded_dm = dm.hpad((1, 1)) # Pad 1 left, 1 right
        expected = mat([[0, 1, 0]])
        assert np.array_equal(padded_dm.mat, expected)
        assert padded_dm.shape == (1, 3)

    def test_split_horizontal(self):
        dm = DotMatrix(mat([[1, 2, 3, 4]]))
        split_dms = dm.split(2, axis=1) # Split into 2 matrices horizontally
        assert len(split_dms) == 2
        assert np.array_equal(split_dms[0].mat, mat([[1, 2]]))
        assert np.array_equal(split_dms[1].mat, mat([[3, 4]]))

    def test_split_vertical(self):
        dm = DotMatrix(mat([[1], [2], [3], [4]]))
        split_dms = dm.split(2, axis=0) # Split into 2 matrices vertically
        assert len(split_dms) == 2
        assert np.array_equal(split_dms[0].mat, mat([[1], [2]]))
        assert np.array_equal(split_dms[1].mat, mat([[3], [4]]))
    
    def test_split_indices_horizontal(self):
        dm = DotMatrix(mat([[1, 2, 3, 4, 5, 6]]))
        # Split at columns 2 and 4
        split_dms = dm.split(np.array([2,4]), axis=1)
        assert len(split_dms) == 3
        assert np.array_equal(split_dms[0].mat, mat([[1,2]]))
        assert np.array_equal(split_dms[1].mat, mat([[3,4]]))
        assert np.array_equal(split_dms[2].mat, mat([[5,6]]))


    def test_add(self):
        dm1 = DotMatrix(mat([[1, 2]]))
        dm2 = DotMatrix(mat([[3, 4]]))
        result_dm = dm1 + dm2
        expected = mat([[1, 2, 3, 4]])
        assert np.array_equal(result_dm.mat, expected)
        # Original should not be modified
        assert np.array_equal(dm1.mat, mat([[1, 2]]))

    def test_iadd(self):
        dm1 = DotMatrix(mat([[1, 2]]))
        dm2 = DotMatrix(mat([[3, 4]]))
        dm1 += dm2
        expected = mat([[1, 2, 3, 4]])
        assert np.array_equal(dm1.mat, expected)

    def test_rshift(self):
        dm = DotMatrix(mat([[1, 2, 3]]))
        shifted_dm = dm >> 1
        expected = mat([[3, 1, 2]])
        assert np.array_equal(shifted_dm.mat, expected)
        # Original should not be modified
        assert np.array_equal(dm.mat, mat([[1, 2, 3]]))

    def test_irshift(self):
        dm = DotMatrix(mat([[1, 2, 3]]))
        dm >>= 1
        expected = mat([[3, 1, 2]])
        assert np.array_equal(dm.mat, expected)

    def test_lshift(self):
        dm = DotMatrix(mat([[1, 2, 3]]))
        shifted_dm = dm << 1
        expected = mat([[2, 3, 1]])
        assert np.array_equal(shifted_dm.mat, expected)
        # Original should not be modified
        assert np.array_equal(dm.mat, mat([[1, 2, 3]]))

    def test_ilshift(self):
        dm = DotMatrix(mat([[1, 2, 3]]))
        dm <<= 1
        expected = mat([[2, 3, 1]])
        assert np.array_equal(dm.mat, expected)

    def test_invert(self):
        dm = DotMatrix(mat([[1, 0], [255, 4]])) # Using various non-zero for "on"
        inverted_dm = ~dm
        # ~1 (00000001) -> 254 (11111110)
        # ~0 (00000000) -> 255 (11111111)
        # ~255 (11111111) -> 0 (00000000)
        # ~4 (00000100) -> 251 (11111011)
        expected = mat([[254, 255], [0, 251]])
        assert np.array_equal(inverted_dm.mat, expected)
        # Original should not be modified
        assert np.array_equal(dm.mat, mat([[1, 0], [255, 4]]))

    def test_str_representation(self):
        dm = DotMatrix(mat([[1, 0], [0, 1]]))
        # String representation uses '⚪' for on (non-zero) and '⚫' for off (zero)
        expected_str = "\n⚪⚫\n⚫⚪"
        assert str(dm) == expected_str

    def test_repr_representation(self):
        dm = DotMatrix(mat([[1, 0], [0, 1]]))
        assert repr(dm) == "DotMatrix(shape=(2, 2))"

    def test_add_incompatible_height(self):
        dm1 = DotMatrix(mat([[1,2]]))      # height 1
        dm2 = DotMatrix(mat([[3,4],[5,6]])) # height 2
        with pytest.raises(ValueError): # numpy concatenate raises ValueError
            _ = dm1 + dm2
            
    def test_split_impossible(self):
        dm = DotMatrix(mat([[1,2,3,4,5]]))
        with pytest.raises(ValueError): # numpy split raises ValueError
            _ = dm.split(2, axis=1) # Cannot split 5 columns into 2 equal parts
            
    def test_empty_matrix_init(self):
        dm = DotMatrix.from_shape((0,0))
        assert dm.shape == (0,0)
        assert dm.width == 0
        assert dm.height == 0
        
    def test_empty_matrix_operations(self):
        dm_empty = DotMatrix.from_shape((0,5)) # 0 rows, 5 cols
        dm_other = DotMatrix.from_shape((0,3))
        
        dm_sum = dm_empty + dm_other
        assert dm_sum.shape == (0,8)
        
        dm_padded = dm_empty.pad(((1,1),(1,1)))
        assert dm_padded.shape == (2,7)
        assert np.array_equal(dm_padded.mat, np.zeros((2,7)))
        
        dm_shifted = dm_empty >> 1
        assert dm_shifted.shape == (0,5)

        inverted_empty = ~dm_empty
        assert inverted_empty.shape == (0,5)

        split_empty = dm_empty.split(1, axis=1) # Should split into 1 of itself
        assert len(split_empty) == 1
        assert split_empty[0].shape == (0,5)
        
        # Test split on an empty matrix with sections
        dm_empty_sections = DotMatrix.from_shape((5,0))
        split_empty_sections = dm_empty_sections.split(np.array([]), axis=0)
        assert len(split_empty_sections) == 1
        assert split_empty_sections[0].shape == (5,0)
