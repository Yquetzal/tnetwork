import pkg_resources
import tnetwork as tn

__all__ = ["graph_socioPatterns2012","graph_socioPatterns_Primary_School","graph_socioPatterns_Hospital","graph_GOT"]

def graph_socioPatterns2012(format=None):
    """
    Function that return the graph of interactions between students in 2012, from the SocioPatterns project.
    >>> dg = tn.graph_socioPatterns2012()

    :return:
    """

    resource_package = __name__
    resource_path = '/'.join(('toy_data', 'thiers_2012.csv'))
    fileLocation = pkg_resources.resource_filename(resource_package, resource_path)


    dg = tn.read_interactions(fileLocation,frequency=20,format=format,columns=["time","n1","n2","c1","c2"])
    return dg

# function to add to dyn_graph_sn.py
def graph_socioPatterns_Primary_School(format=None):
    """
    Function that return the graph of interactions between children and teachers, from the SocioPatterns project.
    >>> dg = DynGraphSN.graph_socioPatterns_Primary_School()

    :return:
    """

    resource_package = __name__
    resource_path = '/'.join(('toy_data', 'Primary_School.csv'))
    fileLocation = pkg_resources.resource_filename(resource_package, resource_path)

    dg = tn.read_interactions(fileLocation,frequency=20,format=format,columns=["time","n1","n2","c1","c2"])
    return dg

def graph_socioPatterns_Hospital(format=None):
    """
    Function that return the graph of interactions in the hospital of Lyon between patients and medical staff, from the SocioPatterns project.
    >>> dg = DynGraphSN.graph_socioPatterns_Hospital()

    :return:
    """

    resource_package = __name__
    resource_path = '/'.join(('toy_data', 'Contacts_Hospital.csv'))
    fileLocation = pkg_resources.resource_filename(resource_package, resource_path)

    dg = tn.read_interactions(fileLocation,frequency=20,format=format,columns=["time","n1","n2","c1","c2"])
    return dg

def graph_GOT():
    """
    Return Game of Thrones temporal network

    See: https://figshare.com/articles/TV_Series_Networks_of_characters/2199646/11

    :return:
    """
    resource_package = __name__
    resource_path = '/'.join(('toy_data', 'GoT_dyn_ts10'))
    fileLocation = pkg_resources.resource_filename(resource_package, resource_path)
    dg = tn.read_snapshots(fileLocation,prefix="GoT_SXXEXX_")
    return dg