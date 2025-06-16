# imports
import os

import pandas as pd
import piexif
from PIL import Image



# define folder paths
directory_path = r"C:\Users\Edward Graham\Desktop\TestImages"  # path to TestImages folder

# set directory_path variable as working directory
os.chdir(directory_path)

# read in csv
csv_path = os.path.join(directory_path, "Test_Photo_Database_Log.csv")
data = pd.read_csv(csv_path)


# helper: convert decimal degrees to EXIF DMS rational format   Tuples required
def deg_to_dms_rational(deg_float):
    """
    Convert a decimal degree value (float) to the EXIF-friendly
    DMS (degrees, minutes, seconds) rational format:
    ((deg, 1), (min, 1), (sec_numerator, sec_denominator)).
    """
    deg_abs = abs(deg_float)
    degrees = int(deg_abs)
    minutes_float = (deg_abs - degrees) * 60
    minutes = int(minutes_float)
    seconds_float = (minutes_float - minutes) * 60
    # Scale seconds into a rational. Here we multiply by 100 to preserve two decimals.
    sec_num = int(round(seconds_float * 100))
    sec_den = 100
    return ((degrees, 1), (minutes, 1), (sec_num, sec_den))


# iterate over each row in the CSV
for idx, row in data.iterrows():
    # debug: show row contents
    # print(f">>> Starting row {idx}: Filename={row.get('Filename')}   Lat={row.get('Latitude')}   Lon={row.get('Longitude')}")

    # Adjust these column names if your CSV uses different headers:
    image_filename = row["Original_File_Name"]          # column that holds the image filename
    latitude = row["Y_coord"]                # column that holds decimal latitude
    longitude = row["X_coord"]              # column that holds decimal longitude

    # check that lat/lon are valid floats
    try:
        latitude = float(latitude)
        longitude = float(longitude)
    except Exception:
        print(f"    [!] Invalid lat/lon at row {idx}: lat='{row['Latitude']}', lon='{row['Longitude']}'. Skipping.")
        continue

    image_path = os.path.join(directory_path, image_filename)

    # check that the file actually exists
    exists = os.path.isfile(image_path)
    # print(f"    Checking file: {image_path} → exists? {exists}")
    if not exists:
        print(f"    [!] File not found. Skipping row {idx}.")
        continue

    # Load existing EXIF (if any). If no EXIF or invalid, initialize empty EXIF dict.
    try:
        exif_dict = piexif.load(image_path)
    except Exception:
        exif_dict = {"0th": {}, "Exif": {}, "GPS": {}, "1st": {}, "thumbnail": None}

    gps_ifd = exif_dict.get("GPS", {})

    # Check if GPSLatitude already exists in EXIF. If so, skip this image.
    if gps_ifd.get(piexif.GPSIFD.GPSLatitude) is not None:
        print(f"    Already has GPS. Skipping {image_filename}.")
        continue

    # Determine reference letters
    lat_ref = "N" if latitude >= 0 else "S"
    lon_ref = "E" if longitude >= 0 else "W"

    # Convert to EXIF DMS rational format
    lat_dms = deg_to_dms_rational(latitude)
    lon_dms = deg_to_dms_rational(longitude)

    # Populate the GPS IFD
    gps_ifd[piexif.GPSIFD.GPSLatitudeRef] = lat_ref.encode()
    gps_ifd[piexif.GPSIFD.GPSLatitude] = lat_dms
    gps_ifd[piexif.GPSIFD.GPSLongitudeRef] = lon_ref.encode()
    gps_ifd[piexif.GPSIFD.GPSLongitude] = lon_dms

    # Update the EXIF dict’s GPS section
    exif_dict["GPS"] = gps_ifd
    exif_bytes = piexif.dump(exif_dict)

    # Wrap the insert in try/except so the script keeps going
    try:
        piexif.insert(exif_bytes, image_path)
        print(f"    [OK] Inserted GPS into {image_filename}.")
    except Exception as e:
        print(f"    [ERROR] Could not insert into {image_filename}: {e}")
        continue
    """
    for img_path in list_of_image_paths:
    orig_name = os.path.basename(img_path)
    try:
        # ← your existing code to insert coords …
        # ← your existing code to rename the file …
        new_name = os.path.basename(renamed_path)

        # record success
        logger.writerow([
            datetime.now().isoformat(),
            orig_name,
            new_name,
            True,
            ""
        ])

    except Exception as e:
        # record failure (no rename or coords)
        logger.writerow([
            datetime.now().isoformat(),
            orig_name,
            "",
            False,
            str(e)
        ])
    """

