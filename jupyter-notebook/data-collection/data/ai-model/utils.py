import os
from pathlib import Path
from typing import List, Tuple, Optional
import pandas as pd
import numpy as np

def read_recordings(
    base_dir: str,
    pattern: str = "test_*",
    sensor_cols: Optional[List[str]] = None,
    label_keywords: Tuple[str, str] = ("walk", "fall"),
    verbose: bool = True
) -> Tuple[List[np.ndarray], List[str], List[str], List[str]]:
    """
    پیمایش base_dir برای پوشه‌هایی با الگوی pattern، خواندن هر .csv و
    تبدیل هر فایل به یک آرایه numpy (n_rows x n_features).
    
    خروجی:
      recordings: لیستی از آرایه‌ها (هر آرایه = یک رکوردینگ)
      labels: لیستی از لیبل‌ها ('Walk', 'Fall', یا 'Unknown')
      file_names: لیستی از نام فایل‌ها (بدون پسوند)
      main_folders: لیستی از نام پوشه مبدا برای هر فایل

    پارامترها:
      base_dir: مسیر اصلی (string یا Path)
      pattern: الگوی پوشه (پیش‌فرض "test_*")
      sensor_cols: لیست نام ستون‌هایی که می‌خواهی بگیری (اگر None، از acc_x..gyro_z استفاده می‌شود)
      label_keywords: tuple از دو کلمه برای تشخیص walk و fall (case-insensitive)
      verbose: اگر True، پیشرفت را چاپ می‌کند
    """
    base = Path(base_dir)
    if sensor_cols is None:
        sensor_cols = ["acc_x", "acc_y", "acc_z", "gyro_x", "gyro_y", "gyro_z"]

    recordings = []
    labels = []
    file_names = []
    main_folders = []
    counter = 0

    folders = sorted(base.glob(pattern))
    total_files_est = 0
    # شمار تقریبی فایل‌ها (اختیاری برای اطلاع)
    for f in folders:
        if f.is_dir():
            total_files_est += len(list(f.glob("*.csv")))

    for folder in folders:
        if not folder.is_dir():
            continue
        for file in sorted(folder.glob("*.csv")):
            try:
                df = pd.read_csv(file)
                if df.empty:
                    if verbose:
                        print(f"⚠️ skipped empty file: {file}")
                    continue

                # مطمئن شو ستون‌های خواسته شده وجود دارن؛ در غیر این صورت تلاش کن تا نزدیک‌ترین ستونهارو برداری
                missing = [c for c in sensor_cols if c not in df.columns]
                if missing:
                    # اگر ستون‌ها نبودن، سعی می‌کنیم حداقل 6 ستون اول عددی را برداریم (ساده و مقاوم)
                    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
                    if len(numeric_cols) >= len(sensor_cols):
                        chosen_cols = numeric_cols[:len(sensor_cols)]
                        if verbose:
                            print(f"ℹ️ file {file.name}: columns {sensor_cols} not all found, using {chosen_cols} instead.")
                    else:
                        # اگر ستون‌های عددی کم بود، رد کن
                        if verbose:
                            print(f"❌ file {file.name}: required columns {sensor_cols} missing and not enough numeric cols -> skipped")
                        continue
                else:
                    chosen_cols = sensor_cols

                # استخراج داده‌ها به صورت numpy (rows x features)
                arr = df[chosen_cols].to_numpy()
                if arr.size == 0:
                    if verbose:
                        print(f"⚠️ file {file.name} produced empty array -> skipped")
                    continue

                # نام فایل و لیبل‌گذاری ساده بر اساس اسم فایل
                fname = file.stem  # بدون .csv
                fname_lower = fname.lower()
                walk_kw, fall_kw = label_keywords[0].lower(), label_keywords[1].lower()
                if walk_kw in fname_lower:
                    label = "Walk"
                elif fall_kw in fname_lower:
                    label = "Fall"
                else:
                    label = "Unknown"

                recordings.append(arr)
                labels.append(label)
                file_names.append(fname)
                main_folders.append(folder.name)

                counter += 1
                if verbose:
                    print(f"\rProcessed: {counter}/{total_files_est} files", end="")

            except Exception as e:
                if verbose:
                    print(f"\n❌ Error reading {file}: {e}")

    if verbose:
        print(f"\n\n✅ Done. Total recordings: {len(recordings)}")
        counts = {l: labels.count(l) for l in set(labels)}
        print(f"Labels counts: {counts}")
    return recordings, labels, file_names, main_folders