from sqlalchemy import select
from sqlalchemy.orm import Session

from models.category import Category
from models.product import Product
from models.saved_product import SavedProduct
from schemas.product import ProductCreate, ProductRead, SavedProductRead


def get_or_create_category(db: Session, name: str | None) -> Category | None:
    if not name:
        return None

    category = db.scalar(select(Category).where(Category.name == name))
    if category is not None:
        return category

    category = Category(name=name)
    db.add(category)
    db.flush()
    return category


def get_or_create_product(db: Session, data: ProductCreate) -> Product:
    if data.source_product_id:
        existing = db.scalar(
            select(Product).where(
                Product.source == data.source,
                Product.source_product_id == data.source_product_id,
            )
        )
        if existing is not None:
            return existing

    category = get_or_create_category(db, data.category)

    product = Product(
        name=data.name,
        brand=data.brand,
        category_id=category.id if category else None,
        description=data.description,
        price=data.price,
        currency=data.currency,
        source=data.source,
        source_product_id=data.source_product_id,
        product_url=data.product_url,
        image_url=data.image_url,
    )
    db.add(product)
    db.commit()
    db.refresh(product)
    return product


def to_product_read(db: Session, product: Product) -> ProductRead:
    category_name = None
    if product.category_id is not None:
        category = db.get(Category, product.category_id)
        category_name = category.name if category else None

    return ProductRead(
        id=product.id,
        name=product.name,
        brand=product.brand,
        category=category_name,
        description=product.description,
        price=float(product.price) if product.price is not None else None,
        currency=product.currency,
        source=product.source,
        source_product_id=product.source_product_id,
        product_url=product.product_url,
        image_url=product.image_url,
        created_at=product.created_at,
    )


def save_product(db: Session, user_id: int, data: ProductCreate) -> SavedProduct:
    product = get_or_create_product(db, data)

    existing = db.scalar(
        select(SavedProduct).where(
            SavedProduct.user_id == user_id, SavedProduct.product_id == product.id
        )
    )
    if existing is not None:
        return existing

    saved = SavedProduct(user_id=user_id, product_id=product.id)
    db.add(saved)
    db.commit()
    db.refresh(saved)
    return saved


def list_saved_products(db: Session, user_id: int) -> list[SavedProduct]:
    return list(
        db.scalars(
            select(SavedProduct)
            .where(SavedProduct.user_id == user_id)
            .order_by(SavedProduct.saved_at.desc())
        )
    )


def unsave_product(db: Session, user_id: int, saved_product_id: int) -> bool:
    saved = db.scalar(
        select(SavedProduct).where(
            SavedProduct.id == saved_product_id, SavedProduct.user_id == user_id
        )
    )
    if saved is None:
        return False
    db.delete(saved)
    db.commit()
    return True


def to_saved_product_read(db: Session, saved: SavedProduct) -> SavedProductRead:
    product = db.get(Product, saved.product_id)
    return SavedProductRead(
        id=saved.id, product=to_product_read(db, product), saved_at=saved.saved_at
    )
