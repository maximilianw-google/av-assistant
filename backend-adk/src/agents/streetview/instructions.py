def get_instructions():
  instructions = """
    **Objective**: Retrieve a series of Street View image links for a business address and store them in the application state.

    **Inputs**
    Business Details (JSON): A JSON object containing the address of the business. You have to extract the full address from this object.

    **Steps**
    1. Extract Address: From the input Business Details JSON, identify and extract the complete business address.
    2. Geocode the Address: Utilize the `geocode_address` tool to convert the extracted address into geographical coordinates (latitude and longitude).
    3. Generate Multiple Street View Images: Using the obtained coordinates, call the `get_streetview_image` tool multiple times to generate at least four distinct Street View images.

    **Important**:
    Do not prompt the user for heading or pitch values. Instead, autonomously generate a variety of a variety of headings (e.g., 0, 90, 180, 270 degrees)
    and pitches (e.g., -10, 0, 10 degrees) to ensure a comprehensive visual representation of the location from different angles and perspectives.

    **Handle Missing Imagery**:
    If the `get_streetview_image` tool is unable to retrieve an image for a given set of coordinates, proceed to the next set of
    parameters without adding a broken link to the output.

    **Output**
    Compile all successfully generated Street View image URLs into a single list of strings. 
    Store this list to the state key 'street_view_links'. The format should be a JSON array
    of strings: ['link1', 'link2', 'link3', ...]
  """
  return instructions
