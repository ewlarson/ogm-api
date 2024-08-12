class CreateDocuments < ActiveRecord::Migration[7.2]
  def change
    create_table :documents do |t|
      t.string :title
      t.jsonb :metadata

      t.timestamps
    end
  end
end
