#!/usr/bin/env python3


import json
import pandas as pd
import matplotlib.pyplot as plt
import os
from pathlib import Path

def load_timing_data(filepath):
    with open(filepath, 'r') as f:
        data = json.load(f)
    return data['records']

def create_operations_csv():
    rtpp_det = load_timing_data('Rtpp/determinize_timing.json')
    rtpp_min = load_timing_data('Rtpp/minimization_timing.json')
    rtpp_inc = load_timing_data('Rtpp/inclusion_timing.json')
    
    wofst_det = load_timing_data('wo_fst/determinize_timing.json')
    wofst_min = load_timing_data('wo_fst/minimization_timing.json')
    wofst_inc = load_timing_data('wo_fst/inclusion_timing.json')
    
    def group_by_pipeline_id(data):
        groups = {}
        for record in data:
            pid = record['pipeline_id']
            if pid not in groups:
                groups[pid] = []
            groups[pid].append(record)
        return groups
    
    def process_directory_data(det_data, min_data, inc_data, prefix):
        det_groups = group_by_pipeline_id(det_data)
        min_groups = group_by_pipeline_id(min_data)
        inc_groups = group_by_pipeline_id(inc_data)
        
        common_ids = set(det_groups.keys()) & set(min_groups.keys()) & set(inc_groups.keys())
        
        rows = []
        for pipeline_id in sorted(common_ids):
            det_ops = det_groups[pipeline_id]
            min_ops = min_groups[pipeline_id] 
            inc_ops = inc_groups[pipeline_id]
            
            if inc_ops:
                row = {
                    f'{prefix}_det_time': None, f'{prefix}_det_size': None,
                    f'{prefix}_min_time': None, f'{prefix}_min_size': None,
                    f'{prefix}_inc_time': inc_ops[0]['elapsed_time'],
                    f'{prefix}_inc_a_size': inc_ops[0]['a_size'],
                    f'{prefix}_inc_b_size': inc_ops[0]['b_size'],
                }
                rows.append(row)
            
            max_ops = max(len(det_ops), len(min_ops), len(inc_ops)-1 if len(inc_ops) > 1 else 0)
            
            for i in range(max_ops):
                row = {}
                
                if i < len(det_ops):
                    row[f'{prefix}_det_time'] = det_ops[i]['elapsed_time']
                    row[f'{prefix}_det_size'] = det_ops[i]['automata_size']
                else:
                    row[f'{prefix}_det_time'] = None
                    row[f'{prefix}_det_size'] = None
                
                if i < len(min_ops):
                    row[f'{prefix}_min_time'] = min_ops[i]['elapsed_time']
                    row[f'{prefix}_min_size'] = min_ops[i]['automata_size']
                else:
                    row[f'{prefix}_min_time'] = None
                    row[f'{prefix}_min_size'] = None
                
                if i+1 < len(inc_ops):
                    row[f'{prefix}_inc_time'] = inc_ops[i+1]['elapsed_time']
                    row[f'{prefix}_inc_a_size'] = inc_ops[i+1]['a_size']
                    row[f'{prefix}_inc_b_size'] = inc_ops[i+1]['b_size']
                else:
                    row[f'{prefix}_inc_time'] = None
                    row[f'{prefix}_inc_a_size'] = None
                    row[f'{prefix}_inc_b_size'] = None
                
                rows.append(row)
        
        return rows
    
    rtpp_rows = process_directory_data(rtpp_det, rtpp_min, rtpp_inc, 'rtpp')
    wofst_rows = process_directory_data(wofst_det, wofst_min, wofst_inc, 'wofst')
    
    max_rows = max(len(rtpp_rows), len(wofst_rows))
    combined_rows = []
    
    for i in range(max_rows):
        row = {}
        
        if i < len(rtpp_rows):
            row.update(rtpp_rows[i])
        else:
            for col in ['rtpp_det_time', 'rtpp_det_size', 'rtpp_min_time', 'rtpp_min_size',
                       'rtpp_inc_time', 'rtpp_inc_a_size', 'rtpp_inc_b_size']:
                row[col] = None
        
        if i < len(wofst_rows):
            row.update(wofst_rows[i])
        else:
            for col in ['wofst_det_time', 'wofst_det_size', 'wofst_min_time', 'wofst_min_size',
                       'wofst_inc_time', 'wofst_inc_a_size', 'wofst_inc_b_size']:
                row[col] = None
        
        combined_rows.append(row)
    
    df = pd.DataFrame(combined_rows)
    df.to_csv('operations_timing.csv', index=False)
    print(f"Created operations_timing.csv with {len(df)} rows (Rtpp: {len(rtpp_rows)}, wo_fst: {len(wofst_rows)})")
    return df

def create_product_csv():
    rtpp_product = load_timing_data('Rtpp/product.json')
    
    rows = []
    for record in rtpp_product:
        row = {
            'product_time': record['elapsed_time'],
            'automaton_size': record['automaton_size'],
            'fst_size': record['fst_size']
        }
        rows.append(row)
    
    df = pd.DataFrame(rows)
    df.to_csv('product_timing.csv', index=False)
    print(f"Created product_timing.csv with {len(df)} rows")
    return df

def create_scatter_plots(ops_df, product_df):
    plt.style.use('default')
    fig, axes = plt.subplots(2, 2, figsize=(12, 10))
    fig.suptitle('Timing Analysis Scatter Plots', fontsize=16)
    
    ax1 = axes[0, 0]
    ax1.scatter(product_df['automaton_size'], product_df['product_time'], 
                alpha=0.6, s=20, color='blue', label='Product')
    ax1.set_xlabel('Automaton Size')
    ax1.set_ylabel('Product Time (s)')
    ax1.set_title('Product Time vs Automaton Size')
    ax1.set_yscale('log')
    ax1.grid(True, alpha=0.3)
    ax1.legend()
    
    ax2 = axes[0, 1]
    rtpp_det_valid = ops_df.dropna(subset=['rtpp_det_size', 'rtpp_det_time'])
    wofst_det_valid = ops_df.dropna(subset=['wofst_det_size', 'wofst_det_time'])
    
    if not rtpp_det_valid.empty:
        ax2.scatter(rtpp_det_valid['rtpp_det_size'], rtpp_det_valid['rtpp_det_time'], 
                    alpha=0.6, s=20, color='red', label='Rtpp')
    if not wofst_det_valid.empty:
        ax2.scatter(wofst_det_valid['wofst_det_size'], wofst_det_valid['wofst_det_time'], 
                    alpha=0.6, s=20, color='green', label='wo_fst')
    ax2.set_xlabel('Automata Size')
    ax2.set_ylabel('Determinization Time (s)')
    ax2.set_title('Determinization Time vs Automata Size')
    ax2.set_yscale('log')
    ax2.grid(True, alpha=0.3)
    ax2.legend()
    
    ax3 = axes[1, 0]
    rtpp_min_valid = ops_df.dropna(subset=['rtpp_min_size', 'rtpp_min_time'])
    wofst_min_valid = ops_df.dropna(subset=['wofst_min_size', 'wofst_min_time'])
    
    if not rtpp_min_valid.empty:
        ax3.scatter(rtpp_min_valid['rtpp_min_size'], rtpp_min_valid['rtpp_min_time'], 
                    alpha=0.6, s=20, color='red', label='Rtpp')
    if not wofst_min_valid.empty:
        ax3.scatter(wofst_min_valid['wofst_min_size'], wofst_min_valid['wofst_min_time'], 
                    alpha=0.6, s=20, color='green', label='wo_fst')
    ax3.set_xlabel('Automata Size')
    ax3.set_ylabel('Minimization Time (s)')
    ax3.set_title('Minimization Time vs Automata Size')
    ax3.set_yscale('log')
    ax3.grid(True, alpha=0.3)
    ax3.legend()
    
    ax4 = axes[1, 1]
    rtpp_inc_valid = ops_df.dropna(subset=['rtpp_inc_a_size', 'rtpp_inc_time'])
    wofst_inc_valid = ops_df.dropna(subset=['wofst_inc_a_size', 'wofst_inc_time'])
    
    if not rtpp_inc_valid.empty:
        ax4.scatter(rtpp_inc_valid['rtpp_inc_a_size'], rtpp_inc_valid['rtpp_inc_time'], 
                    alpha=0.6, s=20, color='red', label='Rtpp')
    if not wofst_inc_valid.empty:
        ax4.scatter(wofst_inc_valid['wofst_inc_a_size'], wofst_inc_valid['wofst_inc_time'], 
                    alpha=0.6, s=20, color='green', label='wo_fst')
    ax4.set_xlabel('First Automata Size')
    ax4.set_ylabel('Inclusion Time (s)')
    ax4.set_title('Inclusion Time vs First Automata Size')
    ax4.set_yscale('log')
    ax4.grid(True, alpha=0.3)
    ax4.legend()
    
    plt.tight_layout()
    plt.savefig('timing_analysis_plots.png', dpi=300, bbox_inches='tight')
    plt.show()
    print("Created timing_analysis_plots.png")

def main():
    os.chdir(Path(__file__).parent)
    
    print("Processing timing data...")
    
    ops_df = create_operations_csv()
    product_df = create_product_csv()
    
    create_scatter_plots(ops_df, product_df)
    
    print("\nSummary:")
    print(f"Operations CSV: {len(ops_df)} records")
    print(f"Product CSV: {len(product_df)} records")
    print("Generated files:")
    print("- operations_timing.csv")
    print("- product_timing.csv") 
    print("- timing_analysis_plots.png")

if __name__ == "__main__":
    main()
