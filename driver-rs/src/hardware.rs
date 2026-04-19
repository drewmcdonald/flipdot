use thiserror::Error;

const START_BYTES_FLUSH: [u8; 2] = [0x80, 0x83];
#[allow(dead_code)]
const START_BYTES_BUFFER: [u8; 2] = [0x80, 0x84];
const END_BYTES: [u8; 1] = [0x8F];

#[derive(Debug, Error)]
pub enum HardwareError {
    #[error("layout must be a non-empty 2D list")]
    EmptyLayout,
    #[error("panel layout must be rectangular")]
    NonRectangularLayout,
    #[error("content height {actual} doesn't match module height {expected}")]
    ModuleHeightMismatch { actual: usize, expected: usize },
    #[error("content width {actual} doesn't match module width {expected}")]
    ModuleWidthMismatch { actual: usize, expected: usize },
    #[error("matrix height {actual} doesn't match panel height {expected}")]
    PanelHeightMismatch { actual: usize, expected: usize },
    #[error("matrix width {actual} doesn't match panel width {expected}")]
    PanelWidthMismatch { actual: usize, expected: usize },
    #[error("frame dimensions ({h}x{w}) don't match panel dimensions ({ph}x{pw})")]
    FrameDimensionMismatch { h: u32, w: u32, ph: u32, pw: u32 },
}

pub fn pack_bits_little_endian(bits: &[u8]) -> Vec<u8> {
    let mut out = Vec::with_capacity(bits.len().div_ceil(8));
    for chunk in bits.chunks(8) {
        let mut byte: u8 = 0;
        for (i, &b) in chunk.iter().enumerate() {
            if b != 0 {
                byte |= 1 << i;
            }
        }
        out.push(byte);
    }
    out
}

#[derive(Debug, Clone)]
pub struct FlippyModule {
    width: usize,
    height: usize,
    address: u8,
    /// Flat row-major content: content[row * width + col].
    content: Vec<u8>,
}

impl FlippyModule {
    pub fn new(width: u32, height: u32, address: u32) -> Self {
        let w = width as usize;
        let h = height as usize;
        Self {
            width: w,
            height: h,
            address: address as u8,
            content: vec![0; w * h],
        }
    }

    pub fn set_content(&mut self, content: &[Vec<u8>]) -> Result<(), HardwareError> {
        if content.len() != self.height {
            return Err(HardwareError::ModuleHeightMismatch {
                actual: content.len(),
                expected: self.height,
            });
        }
        for row in content {
            if row.len() != self.width {
                return Err(HardwareError::ModuleWidthMismatch {
                    actual: row.len(),
                    expected: self.width,
                });
            }
        }
        self.content.clear();
        for row in content {
            self.content.extend_from_slice(row);
        }
        Ok(())
    }

    pub fn fetch_serial_command(&self, flush: bool) -> Vec<u8> {
        let start = if flush {
            START_BYTES_FLUSH
        } else {
            START_BYTES_BUFFER
        };
        let mut out = Vec::with_capacity(2 + 1 + self.width + END_BYTES.len());
        out.extend_from_slice(&start);
        out.push(self.address);
        // Pack column-wise, top-to-bottom, into one byte per column.
        for col in 0..self.width {
            let mut byte: u8 = 0;
            for row in 0..self.height {
                if self.content[row * self.width + col] != 0 {
                    byte |= 1 << row;
                }
            }
            out.push(byte);
        }
        out.extend_from_slice(&END_BYTES);
        out
    }
}

pub struct Panel {
    modules: Vec<Vec<FlippyModule>>,
    n_rows: usize,
    n_cols: usize,
    module_width: usize,
    module_height: usize,
    total_width: usize,
    total_height: usize,
}

impl Panel {
    pub fn new(
        layout: &[Vec<u32>],
        module_width: u32,
        module_height: u32,
    ) -> Result<Self, HardwareError> {
        if layout.is_empty() || layout[0].is_empty() {
            return Err(HardwareError::EmptyLayout);
        }
        let n_rows = layout.len();
        let n_cols = layout[0].len();
        for row in layout {
            if row.len() != n_cols {
                return Err(HardwareError::NonRectangularLayout);
            }
        }
        let mut modules: Vec<Vec<FlippyModule>> = Vec::with_capacity(n_rows);
        for row in layout {
            let mut module_row = Vec::with_capacity(n_cols);
            for &addr in row {
                module_row.push(FlippyModule::new(module_width, module_height, addr));
            }
            modules.push(module_row);
        }
        let mw = module_width as usize;
        let mh = module_height as usize;
        Ok(Self {
            modules,
            n_rows,
            n_cols,
            module_width: mw,
            module_height: mh,
            total_width: mw * n_cols,
            total_height: mh * n_rows,
        })
    }

    /// Returns (total_height, total_width).
    pub fn dimensions(&self) -> (u32, u32) {
        (self.total_height as u32, self.total_width as u32)
    }

    pub fn set_content(&mut self, matrix: &[Vec<u8>]) -> Result<Vec<u8>, HardwareError> {
        if matrix.len() != self.total_height {
            return Err(HardwareError::PanelHeightMismatch {
                actual: matrix.len(),
                expected: self.total_height,
            });
        }
        for row in matrix {
            if row.len() != self.total_width {
                return Err(HardwareError::PanelWidthMismatch {
                    actual: row.len(),
                    expected: self.total_width,
                });
            }
        }
        for mr in 0..self.n_rows {
            let row_start = mr * self.module_height;
            for mc in 0..self.n_cols {
                let col_start = mc * self.module_width;
                let mut tile: Vec<Vec<u8>> = Vec::with_capacity(self.module_height);
                for r in 0..self.module_height {
                    let row = &matrix[row_start + r][col_start..col_start + self.module_width];
                    tile.push(row.to_vec());
                }
                self.modules[mr][mc].set_content(&tile)?;
            }
        }
        let mut serial = Vec::new();
        for module_row in &self.modules {
            for module in module_row {
                serial.extend(module.fetch_serial_command(true));
            }
        }
        Ok(serial)
    }

    pub fn set_content_from_frame(
        &mut self,
        frame_data: &[u8],
        width: u32,
        height: u32,
    ) -> Result<Vec<u8>, HardwareError> {
        if width as usize != self.total_width || height as usize != self.total_height {
            return Err(HardwareError::FrameDimensionMismatch {
                h: height,
                w: width,
                ph: self.total_height as u32,
                pw: self.total_width as u32,
            });
        }
        let w = width as usize;
        let h = height as usize;
        let mut matrix: Vec<Vec<u8>> = Vec::with_capacity(h);
        let mut bit_idx = 0usize;
        for _ in 0..h {
            let mut row = Vec::with_capacity(w);
            for _ in 0..w {
                let byte_idx = bit_idx / 8;
                let bit_pos = bit_idx % 8;
                let bit = if byte_idx < frame_data.len() {
                    (frame_data[byte_idx] >> bit_pos) & 1
                } else {
                    0
                };
                row.push(bit);
                bit_idx += 1;
            }
            matrix.push(row);
        }
        self.set_content(&matrix)
    }
}
