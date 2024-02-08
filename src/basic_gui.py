import tkinter as tk
from tkinter import filedialog
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
from PIL import Image, ImageTk

class GraphGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Graph GUI")


        self.root.pack_propagate(False) # Prevent widgets from affecting the size of the window

        self.canvas = tk.Canvas(root, width=800, height=600)
        self.canvas.pack(fill=tk.BOTH, expand=True)

        self.load_button = tk.Button(root, text="Load Data", command=self.load_data)
        self.load_button.pack()

        self.load_image_button = tk.Button(root, text="Load Image", command=self.load_image)
        self.load_image_button.pack()

        self.load_labels_button = tk.Button(root, text="Load Labels", command=self.load_labels)
        self.load_labels_button.pack()

        self.select_button = tk.Button(root, text="Select Nodes", command=self.select_nodes)
        self.select_button.pack()

        self.save_button = tk.Button(root, text="Save Groups", command=self.save_groups)
        self.save_button.pack()

        self.select_bbox_button = tk.Button(root, text="Select Bounding Box", command=self.toggle_bbox_selection)
        self.select_bbox_button.pack()

        self.unlabeled_count = None
        self.unlabeled_label = tk.Label(root, text=f'Unlabeled Nodes: {self.unlabeled_count}')
        self.unlabeled_label.pack()
        
        self.update_unlabeled_count()
        
        self.canvas.bind("<MouseWheel>", self.zoom)
        self.canvas.bind("<ButtonPress-2>", self.start_pan)
        self.canvas.bind("<B2-Motion>", self.pan)

        self.zoom_scale = 1.0
        self.pan_start_x = None
        self.pan_start_y = None

        self.canvas.bind("<Configure>", self.resize) # Resize the graph when the window is resized

        self.canvas.bind("<ButtonPress-1>", self.start_selection) # start selection when left mouse button is pressed
        self.canvas.bind("<B1-Motion>", self.update_selection) # update selection as the mouse is moved
        self.canvas.bind("<ButtonRelease-1>", self.end_selection) # end selection when left mouse button is released

        self.selection_rectangle = None # Initialize selection_rectangle attribute
        self.selection_coords = None # Initialize selection_coords attribute
        self.bbox_selection_mode = False  # Initialize bbox_selection_mode attribute
        self.selection_labeling_mode = False  # Initialize selection_labeling_mode attribute
        self.selection_label_rectangle = None # Initialize selection_label_rectangle attribute

        self.unlabeled = []


        self.nodes = {}
        self.groups = {}
        self.selected_nodes = {}

        self.graph_plot = None  # Initialize graph_plot attribute


    def load_data(self):
        self.filename = filedialog.askopenfilename(title="Select File", filetypes=(("CSV files", "*.csv"),("all files", "*.*")))
        self.data = pd.read_csv(self.filename)
        #self.nodes = {row['node']: (row['x'], row['y']) for index, row in self.data.iterrows()}
        self.nodes = self.data['node']
        self.unlabeled = list(self.nodes)
        self.unlabeled_count = len(self.unlabeled)
        self.update_unlabeled_count()
        self.x = self.data['x']
        self.y = self.data['y']
        self.plot_graph()

    def update_unlabeled_count(self):
        # Update the label text with the current unlabeled count
        self.unlabeled_label.config(text=f"Unlabeled Nodes: {self.unlabeled_count}")


    def plot_graph(self):
        #clear canvas
        self.canvas.delete("all")

        # add the image as the background
        if hasattr(self, 'bg_photo'):
            self.canvas.create_image(0, 0, anchor=tk.NW, image=self.bg_photo)

            # get size of loaded image
            img_width = self.bg_image.width
            img_height = self.bg_image.height

            # get size of canvas
            canvas_width = self.canvas.winfo_width()
            canvas_height = self.canvas.winfo_height()

            # calculate the scaling factors
            scale_x = canvas_width 
            scale_y = canvas_height 

        #plot nodes
        for index, row in self.data.iterrows():
            x = scale_x * ((row['x'] - min(self.x))/ (max(self.x) - min(self.x)))
            y = scale_y * ((max(self.y) - row['y'])/ (max(self.y) - min(self.y)))
            self.canvas.create_oval(x-5, y-5, x+5, y+5, fill='red')

        self.canvas.pack()

    def load_image(self):
        image_file = filedialog.askopenfilename(title="Select Image", filetypes=(("PNG files", "*.png"),("all files", "*.*")))
        if image_file:
            self.bg_image = Image.open(image_file)

            # Get the dimensions of the canvas
            canvas_width = self.canvas.winfo_width()
            canvas_height = self.canvas.winfo_height()

            # Resize the image to fit the canvas
            self.bg_image = self.bg_image.resize((canvas_width, canvas_height), Image.Resampling.LANCZOS)
            self.bg_photo = ImageTk.PhotoImage(self.bg_image)
            self.canvas.create_image(0, 0, anchor=tk.NW, image=self.bg_photo)

    def zoom(self, event):
        scale = 1.1 if event.delta > 0 else 0.9
        self.zoom_scale *= scale
        self.canvas.scale("all", event.x, event.y, scale, scale)
        
    def start_pan(self, event):
        self.pan_start_x = event.x
        self.pan_start_y = event.y

    def pan(self, event):
        if self.pan_start_x is not None and self.pan_start_y is not None:
            dx = event.x - self.pan_start_x
            dy = event.y - self.pan_start_y
            self.canvas.scan_dragto(-dx, -dy, gain=1)



    def select_nodes(self):
        self.selection_labeling_mode = True
        

    def label_dialog(self):
        self.label_window = tk.Toplevel(self.root)
        self.label_window.title("Label Nodes")

        tk.Label(self.label_window, text="Enter the label for the selected nodes").pack()

        self.label_entry = tk.Entry(self.label_window)
        self.label_entry.pack()

        # Focus the cursor on the entry field
        self.label_entry.focus_set()

        # bing the return event ot the method
        self.label_entry.bind("<Return>", lambda event: self.assign_label())

        tk.Button(self.label_window, text="Assign Label", command=self.assign_label).pack()

    #TODO warn when overwriting labels
    def assign_label(self):
        label = self.label_entry.get()
        nodes_in_bbox = self.nodes_in_bbox(self.current_node_selection_box)
        for node in nodes_in_bbox:
            self.selected_nodes[node] = label
            self.unlabeled.remove(node)
        self.unlabeled_count = len(self.unlabeled)
        self.label_entry.delete(0, tk.END)
        self.label_window.destroy()
        self.update_unlabeled_count()
        self.plot_nodes_in_bbox(self.selection_rectangle_bbox)

    def save_groups(self):
        if hasattr(self, 'selected_nodes'):
            labels_df = pd.DataFrame({"node": list(self.selected_nodes.keys()), "label": list(self.selected_nodes.values())})
            save_filename = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=(("CSV files", "*.csv"), ("All files", "*.*")))
            if save_filename:
                labels_df.to_csv(save_filename, index=False)
                print("Labels saved scuccessfully")

        else:
            print("No groups to save")

    def nodes_in_bbox(self, bbox):
        nodes = []
        rbbox = self.selection_rectangle_bbox
        min_x, max_x = min(self.x), max(self.x)
        min_y, max_y = min(self.y), max(self.y)
        rbbox_width = rbbox[2] - rbbox[0]
        rbbox_height = rbbox[3] - rbbox[1]

        x = rbbox[0] + rbbox_width * ((self.x - min_x) / (max_x - min_x))
        y = rbbox[1] + rbbox_height * ((max_y - self.y) / (max_y - min_y))

        # Check which nodes fall within the bounding box
        mask = ((x >= bbox[0]) & (x <= bbox[2])) & ((y >= bbox[1]) & (y <= bbox[3]))
   
        nodes = self.nodes[mask]


        return nodes

    def resize(self, event):
        if self.graph_plot is not None:
            #self.canvas.itemconfig(self.graph_plot.get_tk_widget(), width=event.width, height=event.height)
            self.graph_plot.get_tk_widget().configure(width=event.width, height=event.height)

    def start_selection(self, event):
        if self.bbox_selection_mode:
            self.canvas.delete("selection")

            # Save the starting coordinates of the selection
            self.selection_coords = (event.x, event.y)
        
        if self.selection_labeling_mode:
            self.canvas.delete("selection_label")

            # Save the starting coordinates of the selection
            self.selection_label_coords = (event.x, event.y)


    def update_selection(self, event):
        if self.bbox_selection_mode and self.selection_coords:
            # delete previous selection rectangle
            if self.selection_rectangle:
                self.canvas.delete(self.selection_rectangle)

            # get current canvas dimensions
            canvas_width = self.canvas.winfo_width()
            canvas_height = self.canvas.winfo_height()

             # Update selection rectangle coordinates
            x0, y0 = self.selection_coords
            x1, y1 = event.x, event.y


            # Ensure that the selection rectangle stays within the canvas bounds
            x0 = max(0, min(x0, canvas_width))
            y0 = max(0, min(y0, canvas_height))
            x1 = max(0, min(x1, canvas_width))
            y1 = max(0, min(y1, canvas_height))

            self.selection_rectangle = self.canvas.create_rectangle(x0, y0, x1, y1, outline="black", tags="selection")

        if self.selection_labeling_mode:
            if self.selection_label_rectangle:
                self.canvas.delete(self.selection_label_rectangle)

            # get current canvas dimensions
            canvas_width = self.canvas.winfo_width()
            canvas_height = self.canvas.winfo_height()

             # Update selection rectangle coordinates
            x0, y0 = self.selection_label_coords
            x1, y1 = event.x, event.y

            self.selection_label_rectangle = self.canvas.create_rectangle(x0, y0, x1, y1, outline="black", tags="selection_label")


    def end_selection(self, event):
        if self.bbox_selection_mode and self.selection_coords:
            # get coordinates of the selection rectangle
            x0, y0 = self.selection_coords
            x1, y1 = event.x, event.y

            # create a bounding box based on selection
            bbox = (min(x0, x1), min(y0, y1), max(x0, x1), max(y0, y1))

            # plot nodes within the bounding box
            self.plot_nodes_in_bbox(bbox)


            # reset selection
            self.selection_coords = None
            self.selection_rectangle = self.canvas.create_rectangle(x0, y0, x1, y1, outline="black", tags="selection")
            self.selection_rectangle_bbox = bbox

        if self.selection_labeling_mode:
            # get coordinates of the selection rectangle
            x0, y0 = self.selection_label_coords
            x1, y1 = event.x, event.y

            # create a bounding box based on selection
            bbox = (min(x0, x1), min(y0, y1), max(x0, x1), max(y0, y1))

            self.current_node_selection_box = bbox
            # open a dialog to label the selected nodes
            self.label_dialog()

            # reset selection
            self.selection_label_coords = None
            self.selection_label_rectangle = None


    def plot_nodes_in_bbox(self, bbox):
        # clear the canvas
        self.canvas.delete("all")

        # add the image as the background
        if hasattr(self, 'bg_photo'):
            self.canvas.create_image(0, 0, anchor=tk.NW, image=self.bg_photo)

        # plot nodes in the bounding box
        for index, row in self.data.iterrows():
            node = row['node']
            x = bbox[0] + (bbox[2] - bbox[0]) * ((row['x'] - min(self.x))/ (max(self.x) - min(self.x)))
            y = bbox[1] + (bbox[3] - bbox[1]) * ((max(self.y) - row['y'])/ (max(self.y) - min(self.y)))

            if node in self.unlabeled:
                self.canvas.create_oval(x-2, y-2, x+2, y+2, fill='red')
            else:
                self.canvas.create_oval(x-2, y-2, x+2, y+2, fill='white')

    def toggle_bbox_selection(self):
        self.bbox_selection_mode = not self.bbox_selection_mode
        if self.bbox_selection_mode:
            self.select_bbox_button.config(text="Cancel Bounding Box Selection")
        else:
            self.select_bbox_button.config(text="Select Bounding Box")

    def load_labels(self):
        label_file = filedialog.askopenfilename(title="Select Label File", filetypes=(("CSV files", "*.csv"), ("All files", "*.*")))
        if label_file:
            labels_df = pd.read_csv(label_file)
            self.selected_nodes = dict(zip(labels_df['node'], labels_df['label']))
            self.unlabeled = [node for node in self.nodes if node not in self.selected_nodes]
            self.unlabeled_count = len(self.unlabeled)
            self.update_unlabeled_count()
            self.plot_nodes_in_bbox(self.selection_rectangle_bbox)  # Update the graph to reflect the loaded labels
            

if __name__ == "__main__":
    root = tk.Tk()
    app = GraphGUI(root)
    root.mainloop()
