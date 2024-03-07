from celulas_responsaveis.cells.models import Role, ProducerCell, PaymentInfo

member = Role()
member.name = "membro"
member.save()

coordenacao = Role()
coordenacao.name = "coordenacao"
coordenacao.save()

producer_cell = ProducerCell()
producer_cell.name = "Os guri"
producer_cell.slug = "os-guri"
producer_cell.description = "eh eles"
producer_cell.save()

payment_info = PaymentInfo()
payment_info.receiver_name = "Henrique"
payment_info.receiver_contact = "51"
payment_info.pix_key = "paganoix"
payment_info.producer_cell = producer_cell
payment_info.description = "gugu"
payment_info.save()
