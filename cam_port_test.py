import cv2

def find_working_camera(max_index=10):
    print("Checking available camera sources...")
    working_sources = []

    for i in range(max_index):
        cap = cv2.VideoCapture(i)
        if cap is None or not cap.isOpened():
            print(f"Source {i}: Not working")
        else:
            print(f"Source {i}: Working ✅")
            working_sources.append(i)
            cap.release()  # Release if working

    if not working_sources:
        print("No working camera sources found.")
    else:
        print(f"\nWorking camera sources: {working_sources}")
    return working_sources

# Run the function
if __name__ == "__main__":
    find_working_camera(max_index=5)  # Check camera sources 0 to 4
