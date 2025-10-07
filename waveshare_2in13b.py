#!/usr/bin/python
# -*- coding:utf-8 -*-
#4171.46
import epd2in13b
import time
from PIL import Image, ImageDraw, ImageFont
import traceback
import mysql.connector
from mysql.connector import Error
from decimal import Decimal

def fetch_data_from_db(query):
    try:
        connection = mysql.connector.connect(
            host='localhost',
            database='sensor_data',
            user='*****',
            password='******'
        )

        if connection.is_connected():
            cursor = connection.cursor()
            cursor.execute(query)
            result = cursor.fetchone()
            return result[0] if result else None

    except Error as e:
        print(f"Error reading data from MySQL table: {e}")
        return None
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

try:
    epd = epd2in13b.EPD()
    epd.init()
    print("Clear...")
    epd.Clear()

    print("Drawing")
    # Drawing on the Horizontal image
    HBlackimage = Image.new('1', (epd2in13b.EPD_HEIGHT, epd2in13b.EPD_WIDTH), 255)  # 298*126
    HRedimage = Image.new('1', (epd2in13b.EPD_HEIGHT, epd2in13b.EPD_WIDTH), 255)  # 298*126

    drawblack = ImageDraw.Draw(HBlackimage)
    drawred = ImageDraw.Draw(HRedimage)

    font20 = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', 17)
    font15 = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', 15)
    font7 = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 7)

    # Fetch data from the database
#    gesamt_kwh = fetch_data_from_db("SELECT global_counter FROM stromdata;")
#    day_kwh = fetch_data_from_db("SELECT daily_count FROM stromdata WHERE DATE(timestamp) = CURDATE();")
#    month_kwh = fetch_data_from_db("SELECT monthly_count FROM stromdata WHERE MONTH(timestamp) = MONTH(CURDATE()) AND YEAR(timestamp) = YEAR(CURDATE());")
#    lastmonth_kwh = fetch_data_from_db("SELECT monthly_count FROM stromdata WHERE MONTH(timestamp) = MONTH(CURDATE())-1 AND YEAR(timestamp) = YEAR(CURDATE());")
    # Total energy consumption
#    gesamt_kwh = fetch_data_from_db("SELECT ROUND(dp1 / 100.0 ,2) FROM measurements ORDER BY timestamp DESC LIMIT 1;")
    gesamt_kwh = fetch_data_from_db("SELECT ROUND((dp1 / 100.0) + (4206.18), 2 ) FROM measurements ORDER BY timestamp DESC LIMIT 1;")

    #     Daily energy consumption
    day_kwh = fetch_data_from_db("SELECT ROUND((MAX(dp1) - MIN(dp1)) / 100.0 ,2) AS daily_kwh FROM measurements WHERE DATE(FROM_UNIXTIME(timestamp)) = CURDATE();")

    # Monthly energy consumption
    month_kwh = fetch_data_from_db("SELECT ROUND((MAX(dp1) - MIN(dp1)) / 100.0 ,2) AS monthly_kwh FROM measurements WHERE MONTH(FROM_UNIXTIME(timestamp)) = MONTH(CURDATE()) AND YEAR(FROM_UNIXTIME(timestamp)) = YEAR(CURDATE());")

    # Last month's energy consumption
    lastmonth_kwh = fetch_data_from_db("SELECT ROUND((MAX(dp1) - MIN(dp1)) / 100.0 ,2) AS last_month_kwh FROM measurements WHERE MONTH(FROM_UNIXTIME(timestamp)) = MONTH(CURDATE() - INTERVAL 1 MONTH) AND YEAR(FROM_UNIXTIME(timestamp)) = YEAR(CURDATE() - INTERVAL 1 MONTH);")

    # Print results
    print("Total kWh:", gesamt_kwh)
    print("Today's kWh:", day_kwh)
    print("This Month's kWh:", month_kwh)
    print("Last Month's kWh:", lastmonth_kwh)


    # Use default values if any of the queries return None
    gesamt_kwh = gesamt_kwh if gesamt_kwh is not None else Decimal('0')
    day_kwh = day_kwh if day_kwh is not None else Decimal('0')
    month_kwh = month_kwh if month_kwh is not None else Decimal('0')
    lastmonth_kwh = lastmonth_kwh if lastmonth_kwh is not None else Decimal('0')

    # Static cost value
    kosten = 0.75

    # Calculate costs
    kosten_thismonth = (float(month_kwh) * kosten)
    kosten_lastmonth = (float(lastmonth_kwh) * kosten)
    kosten_thismonth_rounded = round(kosten_thismonth, 2)
    kosten_thismonth_str = f'{kosten_thismonth_rounded} €'
    text_width2, text_height_kwh = drawblack.textsize(kosten_thismonth_str, font=font20)
    kosten_lastmonth_rounded = round(kosten_lastmonth, 2)
    kosten_lastmonth_str = f'{kosten_lastmonth_rounded} €'
    text_width3, text_height_kwh = drawblack.textsize(kosten_lastmonth_str, font=font20)
    kosten_per_kwh = f"{kosten} €/Kwh"
    print("kosten", kosten_thismonth_rounded)
    # Prepare text for display
    gesamt = f"{float(gesamt_kwh)} Kwh"
    text_width, text_height_gesamt = drawblack.textsize(gesamt, font=font15)

    day = f"{float(day_kwh)} Kwh"
    text_width0, text_height_day = drawblack.textsize(day, font=font15)

    month = f"{float(month_kwh)} Kwh"
    text_width1, text_height_month = drawblack.textsize(month, font=font15)

    q = HBlackimage.width - text_width
    r = HBlackimage.width - text_width0 - 20
    x = HBlackimage.width - text_width1
    y = HBlackimage.width - text_width2 - 112
    z = HBlackimage.width - text_width3

    drawred.text((5, 0), 'Stromverbrauch Kosten', font=font15, fill=0)
    drawblack.text((5, 20), 'gesamt:', font=font15, fill=0)
    drawblack.text((q, 20), gesamt, font=font15, fill=0)
    drawblack.text((5, 33), 'Monat:', font=font15, fill=0)
    drawblack.text((r, 33), month, font=font15, fill=0)
    drawblack.text((5, 46), 'Tag:', font=font15, fill=0)
    drawblack.text((x, 46), day, font=font15, fill=0)
    drawblack.text((y, 76), kosten_thismonth_str, font=font20, fill=0)
    drawblack.text((z, 76), kosten_lastmonth_str, font=font20, fill=0)
    drawblack.text((0, 91), kosten_per_kwh, font=font7, fill=0)
    drawblack.line((0, 17, 255, 17), fill=0)
    drawred.line((0, 63, 255, 63), fill=0)
    drawred.line((0, 78, 255, 78), fill=0)
    drawred.line((0, 100, 255, 100), fill=0)
    drawred.line((100, 63, 100, 100), fill=0)
    drawred.text((5, 62), 'this Month   last Month', font=font15, fill=0)

    epd.display(epd.getbuffer(HBlackimage.rotate(180)), epd.getbuffer(HRedimage.rotate(180)))
    epd.sleep()

except:
    print('traceback.format_exc():\n%s', traceback.format_exc())
    exit()
