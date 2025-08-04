import pandas as pd
import os

# 输入类似 "[0]", "[3:2]", ""，返回 RDL 中需要的格式
# Vector width must be greater than zero
def format_bitrange(bitrange: str):
    if bitrange == "[0]":
        return ""  # 单个位不需要 bitrange
    return bitrange

# 根据Excel内的数据生成 SystemRDL的 field 类型
def behavior_to_rdl(fieldname, bitrange, reset, behavior):
    props = []
    # 三种Behavior类型：
    # 写复位：Write_to_Reset 软件写任何值，字段被硬件复位为0（RDL不支持非0复位值）
    # 写1清0：Write1_to_Clear 软件写1会清零
    # 写清0：Write_to_Reset 同写复位
    # Normal: 正常default读写
    if behavior == "write1_to_clear":
        props += ["sw = rw;", "hw = rw;", "we;"]
    elif behavior == "write_to_reset":
        props += ["sw = rw;", "hw = rw;", "woclr;"]
    else:
        props += ["sw = rw;", "hw = r;"]

    props.append(f"reset = {reset};")
    
    # Use ' ' as the separator to join strings in props
    return f"""    field {{
        {' '.join(props)}
    }} {fieldname}{format_bitrange(bitrange)};"""

# 通过Excel sheet (data file) 生成 Systemrdl 代码
def generate_rdl(df):
    lines = ["addrmap top {"]
    grouped = df.groupby("RegName")
    # Return (RegName, DataFrame) tuple
    for reg, rows in grouped:
        lines.append(f"  reg {{")
        # Return (index, RowData) tuple, iterate each row
        for _, row in rows.iterrows():
            line = behavior_to_rdl(row["FieldName"], row["BitRange"], row["Reset"], row["BehaviorType"])
            lines.append(line)
        lines.append(f"  }} {reg} @ {row['Offset']};")
    # Close addrmap group
    lines.append("};")
    return "\n".join(lines)

def main():
    df = pd.read_excel("input.xlsx")
    rdl_code = generate_rdl(df)
    
    os.makedirs("output", exist_ok=True)
    with open("output/regs.rdl", "w") as f:
        f.write(rdl_code)
    
    # 调用 PeakRDL 生成 Verilog
    os.system("peakrdl regblock output/regs.rdl -o output/rtl --cpuif apb3-flat")

if __name__ == "__main__":
    main()
