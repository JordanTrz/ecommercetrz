from django.shortcuts import render, redirect
from django.contrib.auth import login ,logout, authenticate
from django.template import context

from .models import Categoria, Cliente,Producto, Pedido, PedidoDetalle
from django.contrib.auth.models import User

from tienda.carrito import Cart
from tienda.forms import ClienteForm

from django import forms

# Paypal
from django.conf import settings
from paypal.standard.forms import PayPalPaymentsForm

# Create your views here.
def index(request):

  listaProductos = Producto.objects.all()
  listaCategorias = Categoria.objects.all()

  context ={
    'productos':listaProductos,
    'categorias':listaCategorias
  }
  return render(request,'index.html',context)

def productosPorCategoria(request,categoria_id):
  objCategoria = Categoria.objects.get(pk=categoria_id)
  listaProductos = objCategoria.producto_set.all()
  listaCategorias = Categoria.objects.all()
  context = {
    'productos':listaProductos,
    'categorias':listaCategorias
  }

  return render(request,'index.html',context)

def producto(request,producto_id):
  objProducto = Producto.objects.get(pk=producto_id)
  context = {
    'producto':objProducto
  }
  return render(request,'producto.html',context)

def carrito(request):
      return render(request,'carrito.html')

def agregarCarrito(request,producto_id):
      objProducto = Producto.objects.get(id=producto_id)
      carritoProducto = Cart(request)
      carritoProducto.add(objProducto,1)
      print(request.session.get("cart"))
      return render(request,'carrito.html')

def eliminarProductoCarrito(request,producto_id):
  objProducto = Producto.objects.get(id=producto_id)
  carritoProducto = Cart(request)
  carritoProducto.remove(objProducto)
  return render(request,'carrito.html')

def limpiarCarrito(request):
  carritoProducto = Cart(request)
  carritoProducto.clear()
  return render(request,'carrito.html')


# ---------- Vista para login y registro de usuarios ------------%
def loginUsuario(request):

  if request.method == 'POST':
        #Login usuarios
        dataUsuario = request.POST["usuario"]
        dataPassword = request.POST["password"]

        usuarioAuth = authenticate(request,username=dataUsuario,password=dataPassword)
        if usuarioAuth is not None:
              login(request,usuarioAuth)
              return redirect('/cuenta')
        else:
              context = {
                'error':'datos incorrectos'
              }

  return render(request,'login.html')

def cuentaUsuario(request):
    try:
        clienteEditar = Cliente.objects.get(usuario = request.user)
        dataCliente = {'nombre':request.user.first_name,
                    'apellidos':request.user.last_name,
                    'email':request.user.email,
                    'direccion':clienteEditar.direccion,
                    'telefono':clienteEditar.telefono,
                    'usuario':request.user.username}
    except:
        dataCliente = {'nombre':request.user.first_name,
                    'apellidos':request.user.last_name,
                    'email':request.user.email,
                    'usuario':request.user.username}

    frmCliente = ClienteForm(dataCliente)

    context = {
        'frmCliente':frmCliente
    }
    return render(request,'cuenta.html',context)

def crearUsuario(request):
      if request.method == 'POST':
            dataUsuario = request.POST['nuevoUsuario']
            dataPassword = request.POST['nuevoPassword']

            nuevoUsuario = User.objects.create_user(username=dataUsuario,password=dataPassword)
            login(request,nuevoUsuario)
            return redirect('/cuenta')

def actualizarCliente(request):
      if request.method == 'POST':
            frmCliente = ClienteForm(request.POST)
            if frmCliente.is_valid():
                  # Actualizamos el usuario y cliente
                  dataCliente = frmCliente.cleaned_data
                  print(dataCliente)

                  # Actualizamos Usuario
                  actUsuario = User.objects.get(pk=request.user.id)
                  actUsuario.first_name = dataCliente["nombre"]
                  actUsuario.last_name = dataCliente["apellidos"]
                  actUsuario.email = dataCliente["email"]
                  actUsuario.save()
                  try:
                    actCliente = Cliente.objects.get(usuario = request.user)
                    actCliente.direccion = dataCliente["direccion"]
                    actCliente.telefono = dataCliente["telefono"]
                  except:
                    nuevoCliente = Cliente()
                    nuevoCliente.usuario = request.user
                    nuevoCliente.direccion = dataCliente["direccion"]
                    nuevoCliente.telefono = dataCliente["telefono"]
                    nuevoCliente.save()

                  mensaje = "Datos actualizados"
            else:
                  mensaje = "Error al actualizar los datos"

      context = {
        'mensaje':mensaje,
        'frmCliente':frmCliente
      }

      return render(request,'cuenta.html',context)

def logoutUsuario(request):
      logout(request)
      return render(request,'login.html')

# -------------------------------------------------------------------- #
# ------------------------------ PEDIDOS ----------------------------- #
# -------------------------------------------------------------------- #

def registrarPedido(request):
      if request.user.id is not None:
          # Registra el pedido
          clientePedido = Cliente.objects.get(usuario=request.user)
          nuevoPedido = Pedido()
          nuevoPedido.cliente = clientePedido
          nuevoPedido.save()

          # Registramos el detalle del pedido
          carritoPedido = request.session.get('cart')
          totalPedido = 0
          # lstDetallePedido = []

          for key,value in carritoPedido.items():

                productoPedido = Producto.objects.get(pk=value["producto_id"])

                nuevoPedidoDetalle = PedidoDetalle()
                nuevoPedidoDetalle.pedido = nuevoPedido
                nuevoPedidoDetalle.producto = productoPedido
                nuevoPedidoDetalle.cantidad = int(value["cantidad"])
                nuevoPedidoDetalle.save()
                # lstDetallePedido.append(nuevoPedidoDetalle)
                totalPedido += float(value["cantidad"] * float(productoPedido.precio))

          nuevoPedido.total = totalPedido
          nuevoPedido.save()
          # Se crea el boton de pago de PAYPAL
          request.session['paypal_pid'] = nuevoPedido.id
          host = request.get_host()
          paypal_datos = {
            'business':settings.PAYPAL_RECEIVER_EMAIL,
            'amount':'100',
            'item_name':'PEDIDO # ' + str(nuevoPedido.id),
            'invoice':str(nuevoPedido.id),
            'notify_url':'https://' + host + '/' + 'paypal-ipn',
            'return_url':'https://' + host + '/' + 'pedidos'
          }

          formPedidoPaypal = PayPalPaymentsForm(initial=paypal_datos)

          context = {
            'pedido':nuevoPedido,
            'formpaypal':formPedidoPaypal
          }


          carrito = Cart(request)
          carrito.clear()
          # return redirect('/pedidos')
          return render(request,'pago.html',context)

      else:
          return redirect('/login/')

def pedidopagado(request):
      pedidoID = request.session.get['paypal_pid']
      print(pedidoID)
      pedidoEditar = Pedido.objects.get(pk=pedidoID)
      pedidoEditar.estado = 'pagado'
      pedidoEditar.save()
      return redirect('/pedidos')

def pedidos(request):
    context = {}
    if request.user.id is not None:
        #retorna los pedidos del cliente logueado
        clienteFiltro = Cliente.objects.get(usuario=request.user)
        listaPedidos = Pedido.objects.filter(cliente=clienteFiltro)
        context = {
            'pedidos':listaPedidos
        }
    else:
        return redirect('/login')

    return render(request,'pedidos.html',context)
# -------------------------------------------------------------------- #
