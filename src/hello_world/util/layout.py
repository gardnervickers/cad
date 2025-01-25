import build123d as bd

# Layout shapes side-by-side with a 10mm gap for visual clarity
def layout_shapes(shapes: bd.List[bd.Shape]) -> bd.List[bd.Shape]:
    layout = []
    x_offset = 0
    for shape in shapes:
        layout.append(shape.translate((x_offset, 0, 0)))
        x_offset += shape.bounding_box().size.X + 10
    return layout

